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

### 1. 安装（3 行）

```bash
git clone https://github.com/Lumjiel/freellm.git && cd freellm
pip install -e .                              # 零依赖，装完即可 import
cp keys.example.json keys.json                # 下一步填 key
```

装机版（不想要源码目录）：`pip install git+https://github.com/Lumjiel/freellm.git` —— 该方式不含示例文件，`keys.json` 按下面表格手写（只配一个平台即可）。

> ⚠️ **PyPI 上的 `freellm` 不是本项目**（同名已被他人占用）——请勿 `pip install freellm`，会装成别人的包。

### 2. 配置凭证（`keys.json`）

放**当前项目目录**即可；也可用 `FREELLM_KEYS=/path/to/keys.json` 指定（优先级更高）。
字段名必须与代码一致，**照抄 `keys.example.json` 最省事**：

| 平台 | 凭证字段 | 备注 |
|:--|:--|:--|
| `siliconflow` | `key` | 国内直连，建议首选 |
| `cloudflare` | `account_id` + `token` | 两个都要，`account_id` 参与 API 地址拼接 |
| `nvidia` | `key` | — |
| `modelscope` | `token_read` | 注意字段名是 `token_read`，**不是** `token` |
| `aliyun` | `api_key` | 可缺省：自动回退读 `~/.bailian/config.json` 或 `DASHSCOPE_API_KEY` |
| `groq` | `key` | 国内需代理：条目里加 `"proxy": "http://127.0.0.1:7897"` |

**最少可用配置**（只配一个平台就能跑）：

```json
{ "siliconflow": { "key": "sk-你的key" } }
```

### 3. 跑通

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
freellm platforms          # 哪些平台凭证解析成功 / 健康状态
freellm models             # 当前可选模型（按优先级）
freellm chat '你好'        # 最小验证：能出字就说明通了
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

## ⚙️ 配置（进阶）

凭证字段见上文「配置凭证」表。其余可选项：

| 项 | 位置 | 说明 |
|:--|:--|:--|
| `base_url` | 平台条目内 | 覆盖默认 API 地址（走中转 / 自建网关时用） |
| `proxy` | 平台条目内 | 单平台代理，如 `groq` 在国内需要 |
| `FREELLM_KEYS` | 环境变量 | 指定 `keys.json` 路径（优先于当前目录） |
| `FREELLM_DEBUG=1` | 环境变量 | 调试日志输出到 stderr |

`keys.json` 已被 `.gitignore` 忽略，不会进版本库。

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
├── keys.example.json       # 🔑 凭证模板（复制为 keys.json 再填）
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
