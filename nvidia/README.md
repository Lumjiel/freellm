# NVIDIA NIM 免费 API

> 更新时间：2026-07-21
> Endpoint：`https://integrate.api.nvidia.com/v1`
> 鉴权方式：`nvapi-xxx` 密钥（已记录到 `keys.json`）
> ⚠️ API Key 存于 `keys.json`（本地文件，不跟踪 Git），脚本从 JSON 读取

---

## 一、快速命令

### 查询可用模型

```bash
# 全部模型列表
curl -s "$NVIDIA_API_BASE/models" -H "Authorization: Bearer $NVIDIA_API_KEY"

# 只打印模型 ID
python -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data']]"
```

### 对话推理

```bash
# 基础调用
curl "$NVIDIA_API_BASE/chat/completions" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta/llama-3.1-8b-instruct",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 2048,
    "temperature": 0.7
  }'

# 流式输出
curl "$NVIDIA_API_BASE/chat/completions" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta/llama-3.1-8b-instruct",
    "messages": [{"role":"user","content":"hi"}],
    "max_tokens": 2048,
    "stream": true
  }'
```

### 嵌入向量

```bash
curl "$NVIDIA_API_BASE/embeddings" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nvidia/nv-embedqa-e5-v5",
    "input": "需要向量化的文本"
  }'
```

---

## 二、已验证可用模型（2026-07-21 全量扫描）

> 全量扫描 118 个模型，实测 **30 个**可通过 chat/completions 免费调用。
> 扫描脚本：`scripts/nvidia-scan-models.py`

### 📋 完整可用列表

| 模型 ID | 来源 | 说明 | 权重 |
|:--------|:----|:----|:----:|
| `abacusai/dracarys-llama-3.1-70b-instruct` | Abacus AI | Llama 3.1 70B 微调 | 🔴 超大 |
| `deepseek-ai/deepseek-v4-flash` | DeepSeek | 轻量版 | 🟡 中型 |
| `deepseek-ai/deepseek-v4-pro` | DeepSeek | 完整版 | 🔴 超大 |
| `google/gemma-2-2b-it` | Google | 轻量对话 | 🟢 轻量 |
| `google/gemma-3n-e2b-it` | Google | Gemma 3 nano | 🟢 轻量 |
| `google/gemma-3n-e4b-it` | Google | Gemma 3 nano 4B | 🟢 轻量 |
| `meta/llama-3.1-8b-instruct` | Meta | 经典 8B | 🟡 中型 |
| `meta/llama-3.1-70b-instruct` | Meta | 经典 70B | 🔴 超大 |
| `meta/llama-3.2-11b-vision-instruct` | Meta | 视觉多模态 | 🟡 视觉 |
| `minimaxai/minimax-m2.7` | MiniMax | 国产大模型 | 🟡 中型 |
| `mistralai/mistral-nemotron` | Mistral | NVIDIA 合作版 | 🔴 超大 |
| `mistralai/mistral-small-4-119b-2603` | Mistral | 2026 新版 | 🔴 超大 |
| `mistralai/mixtral-8x7b-instruct-v0.1` | Mistral | MoE 架构 | 🟡 中型 |
| `nvidia/llama-3.1-nemotron-nano-vl-8b-v1` | NVIDIA | 视觉语言 | 🟡 视觉 |
| `nvidia/llama-3.3-nemotron-super-49b-v1` | NVIDIA | 49B 旗舰 | 🔴 超大 |
| `nvidia/llama-3.3-nemotron-super-49b-v1.5` | NVIDIA | v1.5 升级版 | 🔴 超大 |
| `nvidia/nemotron-3-nano-30b-a3b` | NVIDIA | 30B 高效 | 🟡 中型 |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | NVIDIA | 推理优化 | 🟡 中型 |
| `nvidia/nemotron-3-super-120b-a12b` | NVIDIA | 120B 超大 | 🔴 超大 |
| `nvidia/nemotron-3-ultra-550b-a55b` | NVIDIA | **550B 旗舰** | 🔴 超大 |
| `nvidia/nemotron-mini-4b-instruct` | NVIDIA | 轻量首选 | 🟢 轻量 |
| `nvidia/nemotron-nano-12b-v2-vl` | NVIDIA | 12B 视觉 | 🟡 视觉 |
| `nvidia/nvidia-nemotron-nano-9b-v2` | NVIDIA | 9B 通用 | 🟡 中型 |
| `openai/gpt-oss-120b` | OpenAI | 开源 120B | 🔴 超大 |
| `openai/gpt-oss-20b` | OpenAI | 开源 20B | 🟡 中型 |
| `poolside/laguna-xs-2.1` | Poolside | 代码模型 | 🟡 中型 |
| `qwen/qwen3-next-80b-a3b-instruct` | Qwen | 通义 80B | 🔴 超大 |
| `sarvamai/sarvam-m` | Sarvam AI | 多语言 | 🟡 中型 |
| `stepfun-ai/step-3.5-flash` | 阶跃星辰 | 国产轻量 | 🟡 中型 |
| `stepfun-ai/step-3.7-flash` | 阶跃星辰 | 国产新版 | 🟡 中型 |
| `thinkingmachines/inkling` | ThinkingMachines | 推理模型 | 🟡 中型 |
| `upstage/solar-10.7b-instruct` | Upstage | 10.7B 通用 | 🟡 中型 |

### 🔴 超大模型（17 个）
- **RPM**：10–20 / 分钟
- **日上限**：1000 次 / 天
- **列表**：llama 70B, deepseek-v4-pro, nemotron-super-49B/120B/ultra-550B, qwen-80B, gpt-oss-120B, mistral-nemotron/small-119B, dracarys-70B
- **注意**：高峰降速明显，易超时，仅在必要时用

### 🟡 中型模型（12 个）
- **RPM**：40 / 分钟
- **日上限**：~14,400 次 / 天
- **列表**：llama 8B, deepseek-v4-flash, nemotron-3-nano-30B, nemotron-nano-9B, mixtral-8x7B, minimax-m2.7, step-3.5/3.7-flash, solar-10.7B, sarvam-m, inkling, laguna-xs
- **主力推荐**：大批量任务优先选

### 🟢 轻量模型（3 个）
- **RPM**：60 / 分钟
- **日上限**：更高，几乎用不完
- **列表**：gemma-2-2b-it, gemma-3n-e2b/e4b, nemotron-mini-4b

---

## 三、限流规则（完整）

### 3.1 每分钟请求上限（RPM）

| 模型权重 | RPM 上限 | 数量 | 代表模型 |
|:--------|:--------:|:----:|:---------|
| 🔴 超大（70B+） | **10–20** | 17 | DeepSeek V4 Pro, Llama 70B, Nemotron Ultra 550B |
| 🟡 中型 | **40** | 12 | Llama 8B, DeepSeek V4 Flash, Step 3.7 Flash |
| 🟢 轻量/嵌入 | **60** | 3 | Gemma 2B, Nemotron Mini 4B |

### 3.2 每分钟 Token 总量（TPM）

| 限制项 | 数值 |
|:------|:----:|
| 全局 TPM | **12,000 tokens / 分钟** |
| 计算方式 | 输入 + 输出合并计算 |
| 超限后果 | 直接 429 |

### 3.3 并发请求限制

| 限制项 | 数值 |
|:------|:----:|
| 同时并发 | **最多 2 个** |
| 超限后果 | 直接拒绝 |

### 3.4 每日总调用上限

| 模型权重 | 日上限 |
|:--------|:------:|
| 🔴 超大模型 | **1000 次 / 天** |
| 🟡 中型模型 | **~14,400 次 / 天** |
| 🟢 小模型 | 更高 |

> 每日上限按**自然日 0 点重置**。多 Key 共享同一账号额度，不叠加。

### 3.5 单次请求限制

| 限制项 | 数值 |
|:------|:----:|
| `max_tokens`（输出） | **≤ 4096**（超限返回 400） |
| 嵌入单条输入 | **≤ 8192 tokens** |
| 嵌入批量 | **≤ 32 段文本** |

---

## 四、实时查询剩余额度

NVIDIA 没有独立配额接口，通过请求响应头读取：

```bash
# 发一条轻量 POST，读取 rate limit 头
curl -sI "$NVIDIA_API_BASE/chat/completions" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"meta/llama-3.1-8b-instruct","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' \
  | grep -E "x-ratelimit"
```

返回字段：

| Header | 说明 |
|:-------|:-----|
| `x-ratelimit-limit` | 当前模型每分钟总配额 |
| `x-ratelimit-remaining` | 本分钟剩余可调用次数 |
| `x-ratelimit-reset` | 多少秒后额度重置 |

---

## 五、HTTP 状态码速查

| 状态码 | 原因 | 处理方案 |
|:------:|:-----|:---------|
| **200** | 正常 | ✅ |
| **400** | `max_tokens` > 4096 / 参数非法 | 调低 max_tokens，截断输入 |
| **401** | 密钥错误 / 未手机验证 / Key 已删除 | 检查 `keys.json`，确认手机已验证 |
| **403** | 违规商用 / 密钥分享 / 批量刷量 | 停止对外服务，否则永久封禁 |
| **404** | 模型 ID 错误 / 未开放免费 | 换已确认可用的模型 |
| **429** | RPM/TPM/日额度超限 | 读 `x-ratelimit-reset`，等对应秒数 |
| **503** | 服务器满载 / 免费通道限流 | 切冷门模型 / 凌晨错峰 |

---

## 六、最佳实践（Agent 适配）

| 场景 | 做法 |
|:-----|:-----|
| 每次请求前 | 读 `x-ratelimit-remaining`，≤5 则排队 |
| 并发控制 | 限制 ≤2 个同时请求 |
| 单次输出 | 设 `max_tokens: 2048`（留缓冲） |
| 批量任务 | 间隔 ≥1.5s，优先用 40 RPM 的中型模型 |
| 收到 429 | 等 `x-ratelimit-reset` 秒后重试 |
| 大模型调用 | 只在必要时用，日常用 8B 级模型 |

---

## 七、账号 & API Key 规则

| 项目 | 说明 |
|:-----|:------|
| 注册要求 | **必须 +86 手机号短信验证**，邮箱不够 |
| 手机号 | **1 个手机号 = 1 个账号**，虚拟号/接码平台封禁 |
| Key 有效期 | 可设 1/6/12 月或 **永不过期** |
| Key 数量 | 一个账号可生成无限个，但**共享额度** |
| Key 查看 | 仅生成时可见，关闭后无法复看，只能删了重建 |
| 违规后果 | 泄露/分享 Key 给多人 → 封 Key 或封号 |

### 禁止行为（踩中即封号）

- ❌ 搭建网站 / 机器人给外部用户使用
- ❌ 大规模批量离线处理（几万条跑数据集）
- ❌ 企业商用、付费产品调用免费接口
- ❌ 多账号刷额度、代理分发 nvapi 密钥

### 允许范围（你完全合规）

- ✅ 个人本地 CLI 脚本
- ✅ 本地 Agent / 代码助手
- ✅ 学习调试、个人问答
- ✅ 本地 RAG 测试

---

## 八、服务限制说明

| 项目 | 说明 |
|:-----|:------|
| SLA | **无** — 免费层不承诺可用性 |
| 高峰时段 | 国内晚 20:00–24:00 易超时 / 503 |
| 服务变更 | NVIDIA 可随时下线免费模型，无通知 |
| 数据隐私 | 请求数据会被收集用于模型优化 |
| 积分体系 | 新账号送 1000 credits，权重正在逐步弱化 |

---

## 九、重要误区

| ❌ 误区 | ✅ 正解 |
|:--------|:--------|
| 没有总 Token 上限 | 每分钟 12000 TPM 硬封顶 |
| 多生成几个 Key 翻倍额度 | 同一账号所有 Key 共享额度 |
| Key 选永久 = 永久无限用 | 平台规则/违规仍可关停 |
| 本地 Docker NIM 和云端互通 | 完全隔离，不占用免费额度 |

---

## 十、接入清单

- [x] 注册 NVIDIA 开发者账号
- [x] 手机号验证
- [x] 生成永久 API Key（已记录到 `keys.json`）
- [x] 验证 API 可用（12+ 模型通过测试）
- [ ] 验证 `x-ratelimit-*` 头是否可读（待 curl -I 确认）
- [ ] 集成到 `check-all.sh`
