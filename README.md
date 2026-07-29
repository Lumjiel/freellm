# freellm — 多平台免费 LLM 统一调用层

> 6 个 AI 平台、免费模型、**档位优先降级**、零外部依赖（纯 Python 标准库）。
> 任何项目一条命令接入，作为最底层的大模型调用层。
> 最后更新：2026-07-23（v0.2.0 — 模型分层 + 档位降级 + 对抗式审查修复 + 单元测试）

---

## 平台总览

| 平台 | 状态 | 免费额度 | keys.json 条目 | 文档 |
|:-----|:----:|:---------|:---------|:-----|
| **硅基流动** | ✅ | 9B 以下永久免费（RPM 1000 / TPM 50000），国内直连 | `siliconflow` | [siliconflow/](siliconflow/) |
| **Cloudflare Workers AI** | ✅ | 10,000 Neurons/天（61 个模型） | `cloudflare` | [cloudflare/](cloudflare/) |
| **NVIDIA NIM** | ✅ | 请求频率限制（30 个免费模型） | `nvidia` | [nvidia/](nvidia/) |
| **ModelScope 魔搭** | ✅ | 每日请求额度（响应头可读剩余） | `modelscope` | [modelscope/](modelscope/) |
| **阿里云百炼** | ✅ | ~977 万 tokens + 多媒体 + 音频（有到期时间） | `aliyun`（可缺省，见下） | [aliyun/](aliyun/) |
| **Groq** | ⚠️ | LPU 高速推理（RPD 14400/1000 按模型），需代理 | `groq` | [groq/](groq/) |

> 默认优先级：siliconflow → cloudflare → nvidia → modelscope → aliyun → groq（groq key 失效暂置末尾）

## 验证状态（2026-07-23）

| 项目 | 结果 |
|:-----|:----:|
| 6 平台 chat（siliconflow/cloudflare/nvidia/modelscope/aliyun） | ✅ 全通 |
| groq chat | ⚠️ 403 Forbidden（key 失效，需重新生成） |
| 多轮对话 | ✅ |
| 流式输出 | ✅ |
| 嵌入向量 | ✅（siliconflow，dim=1024） |
| 坏 key → AuthError 拉黑 | ✅ |
| 代理隔离（groq 走代理 / 其余直连） | ✅ |
| platforms() 诊断 | ✅ 6/6 可用 |

> 🔑 **凭证**：统存 `keys.json`（本地文件，不跟踪 Git）。
> 百炼特殊：`keys.json` 没配 `aliyun.api_key` 时，自动回退读 `~/.bailian/config.json`（bl CLI 登录凭证）→ 环境变量 `DASHSCOPE_API_KEY`。
> 📊 **用量台账**：`python scripts/check-all.py` 查额度并记录到 `usage-log.md`（管理功能，独立于 SDK）。

## 已知局限

零依赖是硬约束（纯 Python 标准库），以下能力不在当前范围：

| 维度 | 状态 | 替代方案 |
|:-----|:----:|:---------|
| 单元测试 | ✅ 44 个 | `python -m unittest discover tests`（stdlib unittest + mock，零依赖） |
| 异步 API | ❌ 不提供 | 上层用 `asyncio.to_thread()` 包装同步调用 |
| Function Calling | ❌ 不处理 | 只透传 `message.content`，不解析 `tool_calls` |
| 结构化输出 | ⚠️ 基础 | 支持 `response_format` 透传，无 schema 校验 |
| 指数退避 | ⚠️ 简化 | 5xx 仅重试 1 次（0.5s），无可配置策略 |
| Token 计数 | ⚠️ 粗估 | 无 tiktoken，`len * 0.75 + 100` 启发式估算 |
| 线程安全 | ⚠️ 无锁 | 健康状态（拉黑/限流）未加锁，多线程需注意 |
| 响应缓存 | ❌ 不做 | 每次走网络，无请求级缓存 |
| 类型标注 | ⚠️ 基础 | Response/Chunk 有 dataclass，完整标注待补全 |

> freellm 定位是**本地 LLM 后端调用层**，不是生产级 API 网关。需要 aiohttp/tiktoken/pydantic 等能力的场景请另选方案。

---

## 快速开始

### 项目集成（一次安装，处处可用）

```bash
# 在项目 venv 里以可编辑模式安装（uv 环境）
uv pip install -e "E:/claudecode/云计算"
# pip 环境同理：pip install -e "E:/claudecode/云计算"
```

```python
from freellm import chat, chat_stream, embed

# 档位优先降级：先试所有平台的最强模型，全挂再试第二档
r = chat("用中文介绍量子计算")
print(r.content, r.platform, r.usage)

# 指定平台：失败直接抛异常，不降级
r = chat("总结全文", platform="siliconflow")

# 多轮对话
r = chat([
    {"role": "user", "content": "1+1=?"},
    {"role": "assistant", "content": "2"},
    {"role": "user", "content": "再加 1 呢"},
])

# 流式输出（第一个 chunk 产出前自动降级，产出后中断透传）
for chunk in chat_stream("数到 5"):
    print(chunk.delta, end="", flush=True)

# 文本向量化：str → list[float]，list[str] → list[list[float]]
vec = embed("需要向量化的文本")
```

### CLI 调试

```bash
python -m freellm platforms                       # 各平台可用性 / 拉黑 / 限流状态
python -m freellm models                          # 各平台模型列表（按档位）
python -m freellm models --live --platform groq   # 实时查询 /v1/models
python -m freellm chat '你好'                      # 自动选平台
python -m freellm chat '你好' --stream --platform groq
python -m freellm embed '测试文本'
FREELLM_DEBUG=1 python -m freellm chat '你好'      # 输出每次尝试的调试日志
```

### 进阶控制

```python
import freellm

freellm.set_priority(["aliyun", "groq", ...])  # 百炼额度快到期？置顶先消耗
freellm.set_model_tiers("siliconflow", [       # 覆盖某平台的模型优先级
    "Qwen/Qwen3-32B", "Qwen/Qwen3-14B", "Qwen/Qwen3-8B",
])
freellm.list_models()                          # 各平台模型优先级列表
freellm.list_models(live=True)                 # 实时查询 /v1/models
freellm.refresh_models("groq")                 # 刷新某平台模型缓存
freellm.platforms()                            # 诊断：可用性 / 健康状态
freellm.reset_health()                         # 清空拉黑 / 限流记录
freellm.reload()                               # keys.json 改过后热加载
```

---

## 降级规则

**档位优先**：先试所有平台的最强模型（T0），全挂再试第二档（T1），以此类推。
同档位内按平台优先级遍历。上下文窗口不够的模型自动跳过。

```
T0: siliconflow.32B → cloudflare.70B → nvidia.70B → modelscope.235B → aliyun.max → groq.70B
T1: siliconflow.14B → cloudflare.32B → nvidia.v4-pro → modelscope.122B → aliyun.plus → ...
T2: ...
```

| 异常 | 触发 | 行为 |
|:-----|:-----|:-----|
| `ModelError` | 404/400 模型不存在 | 同档位换下一个平台 |
| `ContextLengthError` | 400 上下文超长 | 同档位换下一个平台 |
| `AuthError` | 401/403 凭证坏 | 本进程拉黑该平台，所有档位跳过 |
| `RateLimitError` | 429 | 解析 reset 秒数，限流期内跳过 |
| `BadRequestError` | 其余 400 | **直接上抛**（payload 问题，换谁都一样） |
| `ServerError` | 5xx | 同平台重试 1 次（0.5s），仍挂换下家 |
| `NetworkError` | 超时 / 连接失败 | 换下家 |
| `AllPlatformsFailedError` | 全灭 | 上抛，`.errors` 携带各平台失败原因 |

显式 `model=` 时不做任何降级。显式 `platform=`（无 model=）时平台内按档位降级。
健康状态纯进程内，不持久化。

---

## 使用原则

| # | 原则 | 说明 |
|:-:|:-----|:-----|
| 1 | **按到期时间消耗** | 百炼额度先到期先用：`set_priority(["aliyun", ...])`，绝不浪费 |
| 2 | **按复杂度选模型** | 简单 = flash/轻量，复杂 = max/pro（`model=` 覆盖默认） |
| 3 | **用完即停** | 阿里已 30/30 开启，防止意外扣费 |
| 4 | **网页版免费渠道** | tongyi.com 不走 API 额度 |
| 5 | **本地模型兜底** | 开发调试用本地 Ollama，不动免费额度 |
| 6 | **频率限制型平台注意** | Groq/NVIDIA 按 RPM/TPM 限制，非总量，可长期用 |

---

## 新平台接入流程

1. **`freellm/_platforms.py`**：`SPECS` 加一条 `PlatformSpec`（规范名 / 凭证字段 / 默认模型 / base_url / **models 元组**）；`MODEL_META` 加该平台各模型的上下文窗口和最大输出
2. **`keys.json`** 加对应条目
3. **`<平台>/README.md`**：记录端点、鉴权、免费模型列表、全部限流规则（RPM/TPM/RPD/并发）、HTTP 状态码表
4. **根 `README.md`**：更新平台总览表
5. **`DEFAULT_PRIORITY`**：决定该平台在降级链中的位置

OpenAI 兼容端点是硬前提——6 个平台共用一套传输/解析/降级逻辑，非兼容端点不接。

---

## 文件结构

```
📁 云计算/
├── README.md                ← 本文件
├── CLAUDE.md                ← 项目级记忆（架构 + 坑位 + 安全规范）
├── pyproject.toml           ← freellm 包定义（零依赖，可编辑安装）
├── keys.json                ← 🔑 所有平台凭证（不跟踪 Git）
│
├── freellm/                 ← 🎯 SDK 本体（其他项目 import 这个）
│   ├── __init__.py          ← 对外 API：chat / chat_stream / embed / …
│   ├── _core.py             ← 降级控制器 + 健康状态
│   ├── _http.py             ← urllib 传输层（显式代理隔离 + SSE 解析）
│   ├── _platforms.py        ← 6 条平台声明 + 凭证加载
│   ├── _errors.py           ← 异常体系
│   └── __main__.py          ← python -m freellm 调试入口
│
├── aliyun/ nvidia/ cloudflare/ groq/ siliconflow/ modelscope/
│   └── README.md            ← 各平台额度详情 / 限流规则 / curl 命令
│
├── tests/
│   └── test_core.py         ← 🧪 44 个测试（降级/分类/流式边界/健康状态）
│
├── usage-log.md             ← 📊 用量台账（check-all.py 自动写入，勿手编辑）
└── scripts/
    └── check-all.py         ← 🔄 一键查 6 平台额度（管理功能，不属于 SDK）
```
