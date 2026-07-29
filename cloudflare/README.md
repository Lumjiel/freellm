# Cloudflare Workers AI 免费 API

> 更新时间：2026-07-21
> Endpoint：`https://api.cloudflare.com/client/v4`
> 鉴权方式：`CF_API_TOKEN`（已记录到 `keys.json`）
> Account ID：`8f0359b91ba1b8ac77c20e542ccb7114` ✅

---

## 一、凭证

| 变量 | 说明 | 来源 | 状态 |
|:-----|:------|:-----|:----:|
| `CF_API_TOKEN` | Workers AI 专用 Token | 控制台生成 | ✅ `keys.json` |
| `CF_ACCOUNT_ID` | 账户 ID | 控制台右侧 | ✅ `8f0359b...ccb7114` |

### keys.json

```json
{
  "cloudflare": {
    "description": "Cloudflare Workers AI 免费 API",
    "type": "api-token",
    "token": "cfut_ZfvXThYqK7tz2...",
    "account_id": "8f0359b91ba1b8ac77c20e542ccb7114",
    "created": "2026-07-21"
  }
}
```

---

## 二、可用模型

> 共 **61 个模型**，自动查询脚本：`python scripts/cf-list-models.py`

### 💬 Text Generation（对话 LLM，26 个）

| 模型 ID | 来源 | 上下文 | 说明 |
|:--------|:----|:------:|:-----|
| `@cf/openai/gpt-oss-120b` | OpenAI | 128K | 开源 120B |
| `@cf/openai/gpt-oss-20b` | OpenAI | 128K | 开源 20B |
| `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | Meta | 24K | 70B 快速版 |
| `@cf/meta/llama-3.2-11b-vision-instruct` | Meta | 128K | 视觉多模态 |
| `@cf/meta/llama-3.2-3b-instruct` | Meta | 80K | 轻量 |
| `@cf/meta/llama-3.2-1b-instruct` | Meta | 60K | 最轻量 |
| `@cf/meta/llama-3.1-8b-instruct-fp8` | Meta | 32K | 8B 经典 |
| `@cf/meta/llama-4-scout-17b-16e-instruct` | Meta | 131K | Llama 4 |
| `@cf/moonshotai/kimi-k2.6` | Moonshot | 262K | 国产超大 |
| `@cf/moonshotai/kimi-k2.7-code` | Moonshot | 262K | 编程版 |
| `@cf/qwen/qwen3-30b-a3b-fp8` | 通义千问 | 32K | 30B 高效 |
| `@cf/qwen/qwen2.5-coder-32b-instruct` | Qwen | 32K | 代码 |
| `@cf/qwen/qwq-32b` | Qwen | 24K | 推理 |
| `@cf/deepseek-ai/deepseek-r1-distill-qwen-32b` | DeepSeek | 80K | R1 蒸馏 |
| `@cf/nvidia/nemotron-3-120b-a12b` | NVIDIA | 256K | 120B |
| `@cf/google/gemma-7b-it-lora` | Google | 3K | LoRA 版 |
| `@cf/google/gemma-4-26b-a4b-it` | Google | 256K | 26B |
| `@cf/mistralai/mistral-small-3.1-24b-instruct` | Mistral | 128K | 24B |
| `@cf/ibm-granite/granite-4.0-h-micro` | IBM | 131K | Granite 4 |
| `@cf/zai-org/glm-4.7-flash` | 智谱 | 131K | 国产 |
| `@cf/zai-org/glm-5.2` | 智谱 | 262K | 旗舰 |
| `@cf/aisingapore/gemma-sea-lion-v4-27b-it` | AI Singapore | 128K | 27B |

> 💡 还有 4 个 LoRA/测试模型被省略，完整列表见脚本输出。

### 🖼️ Text-to-Image（文生图，11 个）

| 模型 ID | 来源 |
|:--------|:-----|
| `@cf/black-forest-labs/flux-1-schnell` | BFL |
| `@cf/black-forest-labs/flux-2-dev` | BFL |
| `@cf/black-forest-labs/flux-2-klein-9b` | BFL |
| `@cf/black-forest-labs/flux-2-klein-4b` | BFL |
| `@cf/stabilityai/stable-diffusion-xl-base-1.0` | Stability |
| `@cf/bytedance/stable-diffusion-xl-lightning` | 字节跳动 |
| `@cf/lykon/dreamshaper-8-lcm` | 社区 |
| `@cf/leonardo/phoenix-1.0` | Leonardo |
| `@cf/leonardo/lucid-origin` | Leonardo |

### 📐 Text Embeddings（向量嵌入，7 个）

| 模型 ID | 来源 |
|:--------|:-----|
| `@cf/baai/bge-large-en-v1.5` | BAAI |
| `@cf/baai/bge-base-en-v1.5` | BAAI |
| `@cf/baai/bge-small-en-v1.5` | BAAI |
| `@cf/baai/bge-m3` | BAAI |
| `@cf/qwen/qwen3-embedding-0.6b` | Qwen |
| `@cf/google/embeddinggemma-300m` | Google |

### 🎤 其他（语音/翻译/分类等）

| 类型 | 数量 | 代表 |
|:-----|:----:|:-----|
| ASR 语音识别 | 5 | `@cf/openai/whisper-large-v3-turbo` |
| TTS 语音合成 | 4 | `@cf/myshell-ai/melotts` |
| 图像理解 | 2 | `@cf/llava-hf/llava-1.5-7b-hf` |
| 翻译 | 2 | `@cf/meta/m2m100-1.2b` |
| 分类 | 2 | `@cf/baai/bge-reranker-base` |

---

## 三、快速命令

### 对话推理

```bash
# Workers AI 原生 API
curl "$CF_API_BASE/accounts/$CF_ACCOUNT_ID/ai/run/@cf/meta/llama-3.2-1b-instruct" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 1024
  }'

# OpenAI 兼容接口（和 NVIDIA 统一格式）
curl "$CF_API_BASE/accounts/$CF_ACCOUNT_ID/ai/v1/chat/completions" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "@cf/meta/llama-3.2-1b-instruct",
    "messages": [{"role":"user","content":"你好"}]
  }'
```

### 流式输出

```bash
curl "$CF_API_BASE/accounts/$CF_ACCOUNT_ID/ai/run/@cf/meta/llama-3.2-1b-instruct" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stream": true,
    "messages": [{"role":"user","content":"hi"}]
  }'
```

### 向量嵌入

```bash
curl "$CF_API_BASE/accounts/$CF_ACCOUNT_ID/ai/run/@cf/baai/bge-large-en-v1.5" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"需要向量化的文本"}'
```

### 文生图

```bash
curl "$CF_API_BASE/accounts/$CF_ACCOUNT_ID/ai/run/@cf/black-forest-labs/flux-1-schnell" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"a cat"}'
```

### 查询可用模型

```bash
python scripts/cf-list-models.py
```

---

## 四、免费额度规则

### 4.1 Neurons 计量

| 项目 | 数值 |
|:-----|:-----|
| 每日免费 | **10,000 Neurons** |
| 重置时间 | UTC 0:00（北京时间 08:00） |
| 1 Neurons ≈ | 1 Token（实测浮动，取决于模型） |
| 是否可累积 | ❌ 不可，当日清零 |
| 多 Token 翻倍 | ❌ 同一账号共享 |

### 4.2 实测消耗参考

| 模型 | 单次消耗 | 日均可用 |
|:----|:--------:|:--------:|
| `llama-3.2-1b-instruct` | ~0.05 | ~200,000 次 |
| `llama-3.1-8b-fp8` | ~1-5 | ~2,000-10,000 次 |
| `llama-3.3-70b` | ~20-200 | ~50-500 次 |
| Flux 文生图 | ~50-120 | ~80-200 张 |
| 向量嵌入 | ~1-10 | ~1,000-10,000 段 |

> 实测调用 `llama-3.2-1b-instruct` 仅消耗 **0.048 Neurons**，极度便宜。

### 4.3 速率限制

| 模型类型 | RPM | 并发 |
|:---------|:---:|:----:|
| 8B 文本生成 | 300 | 5 |
| 14B/70B 大模型 | 150 | 3 |
| 向量嵌入 | 3000 | 10 |

### 4.4 单次请求限制

| 限制项 | 数值 |
|:------|:-----|
| 上下文总长度 | **≤ 8192 tokens** |
| `max_tokens` 输出 | **≤ 2048**（超限截断） |
| 向量批量 | ≤ 32 段文本 |

---

## 五、查询额度

> ✅ 实测：Cloudflare 在**响应体**中返回 `neurons` 字段，非响应头。

### 方式一：解析每次返回的 neurons 值（推荐）

```bash
# 请求后会返回 usage.neurons
curl -s "$CF_API_BASE/accounts/$CF_ACCOUNT_ID/ai/run/@cf/meta/llama-3.2-1b-instruct" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hi"}],"max_tokens":1}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print(f'本次消耗: {d[\"result\"][\"usage\"][\"neurons\"]:.3f} Neurons')"
```

### 方式二：网页可视化

控制台 → Workers & Pages → AI → Analytics

---

## 六、HTTP 状态码速查

| 状态码 | 原因 | 处理方案 |
|:------:|:-----|:---------|
| **200** | 正常 | ✅ |
| **400** | 上下文超 8K / 参数格式错误 | 核对请求格式 |
| **401** | Token 错误 / 已删除 | 检查 `keys.json` |
| **403** | 权限不足（只有 Read） | 重建 Token，勾选 Read+Edit |
| **404** | 模型 ID 写错 | 先查模型列表 |
| **429** | RPM 超限 / 并发超限 | 增加请求间隔 |
| **503** | 服务器满载 | 换轻量模型 / 错峰 |

> 额度耗尽无专用报错码。等待 UTC 0 点重置。

---

## 七、合规 & 账号

| 项目 | 说明 |
|:-----|:------|
| 注册 | **仅邮箱**，无需手机号/信用卡 |
| Token | 可永久有效，后台可随时删除 |
| SLA | **无** |
| ✅ 允许 | 本地 CLI/Agent/学习调试 |
| ❌ 禁止 | 对外服务/商用/批量刷量/多账号 |

---

## 八、接入清单

- [x] 注册 Cloudflare 账号
- [x] 生成 Workers AI Token ✅
- [x] 记录 Account ID ✅ `8f0359b91ba1b8ac77c20e542ccb7114`
- [x] 查可用模型 ✅ **61 个**
- [x] 验证调用 ✅ 两个端点均可用
- [x] 验证额度查询 ✅ neurons 在响应体中
- [ ] 集成到 `check-all.sh`
