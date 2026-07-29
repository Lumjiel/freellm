# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

**freellm** — 最小 LLM 调用 SDK：6 个免费平台互为备胎，任何项目 `uv pip install -e` 一条命令接入，作为最底层的大模型调用层。零外部依赖（纯标准库 urllib）。只关注"调用"；额度查询/台账（`scripts/check-all.py`）是独立管理功能，不进 SDK。

**v0.2.0 核心变化**：档位优先降级。每平台声明多个免费模型按质量排序（`models` 元组），降级时先试所有平台的 T0（最强），全挂再试 T1，以此类推。SDK 不做智能排序——出厂默认按厂商命名惯例 + 参数量粗排，用户通过 `set_model_tiers()` 覆盖。运行时根据 payload 长度自动排除上下文窗口不够的模型。

| 平台 | keys.json 条目 | 凭证字段 | 备注 |
|:-----|:---------|:---------|:-----|
| groq | `groq` | key + base_url + **proxy** | 唯一需要海外代理的平台 |
| siliconflow | `siliconflow` | key + base_url | 国内直连，嵌入默认平台 |
| cloudflare | `cloudflare` | token + account_id | OpenAI 兼容端点 `/ai/v1`，Neurons/天 |
| nvidia | `nvidia` | key | 直连 |
| modelscope | `modelscope` | token_read + inference_base | 国内直连 |
| aliyun | `aliyun`（可缺省） | api_key | DashScope compatible-mode；fallback 读 `~/.bailian/config.json` → `DASHSCOPE_API_KEY` |

## 常用命令

```bash
# SDK 调试（仓库根目录）
python -m freellm platforms                      # 各平台可用性 / 拉黑 / 限流
python -m freellm models                         # 各平台模型列表（按档位 T0/T1/...）
python -m freellm models --live --platform groq  # 实时查询 /v1/models
python -m freellm chat '你好' [--platform groq] [--stream] [--model M]
python -m freellm embed '文本'
FREELLM_DEBUG=1 python -m freellm chat '你好'    # 每次尝试的调试日志

# 不装包直接测（等价 editable 安装）
uv run --with-editable . python -m freellm platforms

# 额度管理（独立脚本，必须在仓库根目录跑——相对路径读 keys.json）
python scripts/check-all.py

# 单元测试（stdlib unittest + mock，零依赖）
python -m unittest discover tests -v
```

库用法：项目 venv 里 `uv pip install -e "E:/claudecode/云计算"`，然后 `from freellm import chat, chat_stream, embed`。

## 架构

6 平台**全部走 OpenAI 兼容 HTTP**（含百炼 DashScope compatible-mode、Cloudflare `/accounts/{id}/ai/v1`），平台间差异只剩 4 项，收敛为声明：

- **`_platforms.py`**：`SPECS` 里 6 条 `PlatformSpec`（规范名 / 凭证字段 / 默认模型 / base_url 模板 / **models 元组**）。`MODEL_META` 是嵌套 dict（`platform → model → ModelMeta`），记录各模型上下文窗口和最大输出（用于运行时过滤，避免同名模型跨平台冲突）。`set_model_tiers()` / `get_model_tiers()` 管理用户覆盖 > 实时缓存 > 出厂默认的优先级链。`DEFAULT_PRIORITY` 当前为 siliconflow → cloudflare → nvidia → modelscope → aliyun → groq（groq key 失效暂置末尾）。**新增平台 = 加一条声明 + keys.json 加条目 + MODEL_META 加元数据**，其余模块零改动。
- **`_http.py`**：urllib 传输层。**永远显式 opener**——有 proxy 走代理，无 proxy 用 `ProxyHandler({})` 强制直连。`post_json` / `post_sse` / `get_json`（用于 /models 查询）。
- **`_core.py`**：降级控制器。共用前置 `_prepare()`（规范化消息 + 解析候选 + 构建档位列表）、`_iter_candidates()`（按 tier × 平台优先级产出候选，跳过拉黑/限流/窗口不够的）、`_fail()`（候选耗尽终结异常）三个辅助函数，`chat()` 和 `chat_stream()` 只负责发请求和处理响应。**档位优先**：外层按 tier index 遍历，内层按平台优先级遍历。`ModelError` / `ContextLengthError` 为模型级错误（换下一个平台同档模型）；`AuthError` / `RateLimitError` / `NetworkError` 为平台级错误（拉黑/限流后跳过）。`list_models()` / `refresh_models()` 提供模型发现和实时刷新（refresh 保留 curated 顺序，新模型追加末尾）。`_estimate_tokens()` 用 `len * 0.75` 估算中英混合 token 数。
- **`_errors.py`**：`classify(status, message)` 把 HTTP 响应映射到异常类型；404 + "model" → `ModelError`；400 靠精确短语区分上下文超长（"too long"/"token limit" 等）、模型不可用（"not found"/"does not exist" 等）和普通坏请求。注意：`_MODEL_HINTS` 不含 "model" 本身（避免误判），`_CONTEXT_HINTS` 不含 "token"/"length" 等宽泛词。

**流式降级边界**：`chat_stream()` 只在第一个 chunk 产出**前**降级；流开始后中断异常透传给消费方（避免两个平台的 chunk 混流）。流式不做同平台 5xx 重试。

**生成物**：`usage-log.md` 由 check-all.py 每次运行追加一张表（**同日不去重**，勿手工编辑）；`aliyun/usage-history.md` 手工维护账单。

## 历史坑位（旧 client.py 已删，防止回归）

- 百炼**禁止**走 `bl` CLI 子进程——旧实现只发最后一条消息，多轮上下文全丢。已改 DashScope HTTP。
- `platform=` 参数用规范英文名（`aliyun` 不是 `阿里百炼`），未知平台显式报错，不再静默跳过。
- 优先级单一真理源在 `_platforms.DEFAULT_PRIORITY`（旧版 client.py 和 router.py 各存一份）。
- **Windows Store python 空壳 stub**：`C:\Users\JIE\AppData\Local\Microsoft\WindowsApps\python.exe`（Version 0.0.0）在 User PATH 中优先级高于 `E:\develop\scripts`，导致 `python` 命令静默退出、零输出。已修复：将 `E:\develop\scripts` 移到 `WindowsApps` 前面。若重装系统/重置 PATH 后复现，去「设置 → 应用 → 应用执行别名」关掉 `python.exe` / `python3.exe` 别名即可。

## 对抗式审查结论（2026-07-22）

已修复的设计缺陷（防止回归）：

- **MODEL_META 必须嵌套**（`platform → model → Meta`）：同名模型在不同平台上下文窗口不同（如 Qwen3-32B 在 siliconflow 是 32K，modelscope 是 4K），扁平 dict 会键冲突。
- **`_MODEL_HINTS` 不含 "model" 本身**：否则任何 400 含 "model" 都判 ModelError，把 payload 格式错误（BadRequestError）误当模型不可用。
- **`_CONTEXT_HINTS` 不含 "token"/"length" 等宽泛词**：否则 "invalid token"（认证问题）被误判为上下文超长。
- **`refresh_models()` 保留 curated 顺序**：live 列表按字母序，直接替换会摧毁质量排序。正确做法：curated 中仍存在的保持原序 + 新模型追加末尾。
- **SDK 不做智能排序**：模型强弱无法通用量化（任务相关），SDK 只提供机制（档位遍历 + 窗口过滤），排序由用户 `set_model_tiers()` 决定。出厂默认是启发式（命名惯例 + 参数量），不是真理。

## 安全规范

- 🔑 所有 API Key 只存 `keys.json`（gitignore），不硬编码、不写进文档、不打印到日志
- 阿里云日常操作走 `--profile devops`，主账号 AK 仅控制台使用
- 代理规则：groq 走 keys.json 里的 Clash `127.0.0.1:7897`；其余平台强制直连（传输层空 ProxyHandler 保证）

## 新会话启动流程

1. 读根 `README.md`——平台总览 + 降级规则表 + 使用原则（按到期时间消耗、按复杂度选模型）
2. 跑 `python -m freellm platforms` 看各平台现状
3. 动单个平台前先读该平台 README——限流规则和状态码对照都在里面
