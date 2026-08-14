# freellm — 零依赖免费 LLM 统一调用层

**6 个免费平台互为备胎，档位优先降级，纯 Python 标准库零外部依赖。**

*Free LLM API calls with auto-fallback across 6 providers. Zero deps, pure stdlib.*

[快速开始](#-quick-start) · [平台总览](#-平台总览) · [降级规则](#-降级规则) · [API](#-api)

---

## 😤 问题

你想让项目调 LLM，但：

| 方案 | 问题 |
|------|------|
| OpenAI API | $5 起步，国内还需代理 |
| 单一免费平台 | 额度有限、限频、随时可能停 |
| langchain / openai-sdk | 依赖重、绑定单一 provider |

**你需要一个零依赖的统一调用层，6 个免费平台自动备胎，一个挂了秒切下一个。**

---

## ✅ 方案

```
你的代码 → freellm.chat() → 硅基流动 → Cloudflare → NVIDIA → ModelScope → 阿里云 → Groq
                                                    ↓
                                            全挂才报错，自动降级
```

- **档位优先**：先试所有平台最强模型（T0），全挂再试 T1、T2
- **纯标准库**：零外部依赖，`urllib` + `json`，任何 Python 项目直接 import
- **零配置**：`keys.json` 存凭证，git 不跟踪

---

## 🚀 Quick Start

```python
from freellm import chat, chat_stream, embed

# 自动选平台 + 档位降级
r = chat("用中文介绍量子计算")
print(r.content, r.platform, r.usage)

# 流式输出
for chunk in chat_stream("数到 5"):
    print(chunk.delta, end="", flush=True)

# 文本向量化
vec = embed("需要向量化的文本")
```

```bash
# CLI 调试
python -m freellm chat '你好'            # 自动选平台
python -m freellm chat '你好' --stream   # 流式
python -m freellm platforms              # 查看各平台健康状态
python -m freellm models                # 查看模型列表
```

---

## 📊 平台总览

| 平台 | 状态 | 免费额度 | 速度 |
|------|------|----------|------|
| **硅基流动** | ✅ | 9B 以下永久免费（RPM 1000） | ⚡⚡ |
| **Cloudflare** | ✅ | 10,000 Neurons/天（61 模型） | ⚡⚡ |
| **NVIDIA NIM** | ✅ | 30 免费模型（频率限制） | ⚡ |
| **ModelScope** | ✅ | 每日请求额度 | ⚡ |
| **阿里云百炼** | ✅ | ~977 万 tokens（有到期） | ⚡⚡ |
| **Groq** | ⚠️ | LPU 高速推理（需代理） | ⚡⚡⚡ |

**默认优先级**：siliconflow → cloudflare → nvidia → modelscope → aliyun → groq

---

## 📊 功能矩阵

| 功能 | Python API | CLI | 说明 |
|------|-----------|-----|------|
| 基础对话 | `chat()` | `chat 'prompt'` | 自动降级 |
| 流式输出 | `chat_stream()` | `chat --stream` | 首 chunk 产出前自动降级 |
| 多轮对话 | `chat([messages])` | — | 传 message 列表 |
| 文本向量化 | `embed()` | 'embed text' | siliconflow, dim=1024 |
| 指定平台 | `platform=` | `--platform` | 失败直接抛异常 |
| 指定模型 | `model=` | `--model` | 不做降级 |
| 调整优先级 | `set_priority()` | — | 按到期时间消耗额度 |

---

## 🔧 进阶控制

```python
import freellm

# 百炼额度快到期？置顶先消耗
freellm.set_priority(["aliyun", "siliconflow", "cloudflare", ...])

# 覆盖某平台的模型优先级
freellm.set_model_tiers("siliconflow", [
    "Qwen/Qwen3-32B", "Qwen/Qwen3-14B", "Qwen/Qwen3-8B",
])

# 诊断
freellm.platforms()       # 可用性 / 健康状态
freellm.reset_health()    # 清空拉黑 / 限流记录
freellm.reload()          # keys.json 改过后热加载
```

---

## 🔄 降级规则

**档位优先**：先试所有平台最强模型（T0），全挂再试 T1、T2。同档位按平台优先级遍历。上下文窗口不够自动跳过。

| 异常 | 触发 | 行为 |
|------|------|------|
| `ModelError` | 404/400 模型不存在 | 同档位换下一个平台 |
| `ContextLengthError` | 400 上下文超长 | 同档位换下一个平台 |
| `AuthError` | 401/403 凭证坏 | 本进程拉黑该平台 |
| `RateLimitError` | 429 | 解析 reset 秒数，限流期内跳过 |
| `ServerError` | 5xx | 同平台重试 1 次，仍挂换下家 |
| `NetworkError` | 超时/连接失败 | 换下家 |
| `AllPlatformsFailedError` | 全灭 | 上抛，`.errors` 携带各平台失败原因 |

显式 `model=` 时不做任何降级。健康状态纯进程内，不持久化。

---

## ⚙️ 配置

**凭证**：统存 `keys.json`（git 不跟踪）。

| 字段 | 说明 |
|------|------|
| `siliconflow.api_key` | 硅基流动 API Key |
| `cloudflare.account_id` + `api_token` | Cloudflare 凭证 |
| `nvidia.api_key` | NVIDIA NIM Key |
| `modelscope.api_key` | ModelScope Token |
| `aliyun.api_key` | 阿里云百炼 Key（可缺省，回退读 `~/.bailian/config.json`） |
| `groq.api_key` | Groq Key |

**用量台账**：`python scripts/check-all.py` 查额度并记录到 `usage-log.md`。

---

## 📁 项目结构

```
freellm/
├── freellm/               # SDK 本体（其他项目 import 这个）
│   ├── __init__.py        # 对外 API：chat / chat_stream / embed
│   ├── _core.py           # 降级控制器 + 健康状态
│   ├── _http.py           # urllib 传输层（代理隔离 + SSE 解析）
│   ├── _platforms.py      # 6 条平台声明 + 凭证加载
│   └── _errors.py         # 异常体系
├── aliyun/ nvidia/ cloudflare/ groq/ siliconflow/ modelscope/
│   └── README.md          # 各平台额度详情 / 限流规则
├── tests/
│   └── test_core.py       # 44 个测试（降级/流式/健康状态）
├── scripts/
│   └── check-all.py       # 一键查 6 平台额度
├── keys.json              # 🔑 所有平台凭证（git 不跟踪）
├── pyproject.toml         # 包定义（零依赖）
└── CLAUDE.md              # 项目级记忆
```

---

## 🧪 测试

```bash
python -m unittest discover tests   # 44 个测试，纯 stdlib
```

---

## ⚠️ 已知局限

零依赖是硬约束（纯 Python 标准库），以下能力不在当前范围：

| 能力 | 状态 | 替代方案 |
|------|------|----------|
| 异步 API | ❌ | 上层用 `asyncio.to_thread()` 包装 |
| Function Calling | ❌ | 只透传 `message.content` |
| Token 精确计数 | ⚠️ | `len * 0.75 + 100` 启发式估算 |

---

## 📜 License

MIT
