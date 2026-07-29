# SiliconFlow 硅基流动

> 更新时间：2026-07-21
> API Base：`https://api.siliconflow.cn/v1`（OpenAI 标准兼容）
> 网络：✅ 国内直连
> 永久免费：9B 及以下开源模型，需实名认证

---

## 一、凭证

| 变量 | 值 | 状态 |
|:-----|:----|:----:|
| `SILICONFLOW_API_KEY` | `sk-orwsac...knek` | ✅ `keys.json` |
| `SILICONFLOW_BASE_URL` | `https://api.siliconflow.cn/v1` | ✅ |
| 实名认证 | 个人实名 | ✅ 已完成 |
| 账户余额 | -0.55 | ⚠️ 需充值激活 |

> ⚠️ **当前状态**：Key 和实名都可用，但余额为负（-0.55）。
> 可能需要充值 ¥1 以上激活账户，之后免费模型调用费用=0。

---

## 二、可用模型（93 个）

### ✅ 永久免费模型（推荐）

| 模型 ID | 类型 | 说明 |
|:--------|:----|:------|
| `Qwen/Qwen2.5-7B-Instruct` | LLM | 通义千问 7B ⭐ |
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | LLM | DeepSeek R1 蒸馏 |
| `THUDM/glm-4-9b-chat` | LLM | 智谱 GLM 9B |
| `Qwen/Qwen3-8B` | LLM | 千问 3 8B |
| `Qwen/Qwen3-14B` | LLM | 千问 3 14B |
| `Qwen/Qwen3-32B` | LLM | 千问 3 32B |
| `stepfun-ai/Step-3.5-Flash` | LLM | 阶跃星辰 |
| `deepseek-ai/DeepSeek-V4-Flash` | LLM | DeepSeek 轻量 |
| `BAAI/bge-large-zh-v1.5` | 嵌入 | 中文向量 ⭐ |
| `BAAI/bge-large-en-v1.5` | 嵌入 | 英文向量 |
| `BAAI/bge-m3` | 嵌入 | 多语言向量 |
| `Qwen/Qwen3-Embedding-0.6B` | 嵌入 | 轻量向量 |

> ⚠️ 带 `Pro/` 前缀的是收费版本，不要选用。

---

## 三、快速命令

### 查可用模型

```bash
curl -s "$SILICONFLOW_BASE_URL/models" \
  -H "Authorization: Bearer $SILICONFLOW_API_KEY"
```

### 对话推理

```bash
curl "$SILICONFLOW_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $SILICONFLOW_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [
      {"role": "system", "content": "简洁命令行助手"},
      {"role": "user", "content": "你好"}
    ],
    "temperature": 0.7,
    "max_tokens": 1024
  }'
```

### 向量嵌入

```bash
curl "$SILICONFLOW_BASE_URL/embeddings" \
  -H "Authorization: Bearer $SILICONFLOW_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "BAAI/bge-large-zh-v1.5",
    "input": "需要向量化的文本"
  }'
```

---

## 四、查询剩余额度

无独立配额接口。从推理请求的响应头读取：

```bash
curl -sI "$SILICONFLOW_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $SILICONFLOW_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model":"Qwen/Qwen2.5-7B-Instruct",
    "messages":[{"role":"user","content":"hi"}],
    "max_tokens":1
  }' \
  | grep -E "x-ratelimit"
```

| Header | 含义 |
|:-------|:------|
| `x-ratelimit-limit-requests` | RPM 上限 |
| `x-ratelimit-remaining-requests` | 当前分钟剩余 |
| `x-ratelimit-reset-requests` | 重置秒数 |
| `x-ratelimit-limit-tokens` | TPM 上限 |
| `x-ratelimit-remaining-tokens` | 剩余 Token |

---

## 五、免费额度规则

| 项目 | 数值 |
|:-----|:-----:|
| RPM | **1000** |
| TPM | **50,000** |
| 并发 | ≤ 5 |
| RPD | ❌ **无**（滚动限流，可持续用） |
| 免费模型 | 9B 及以下无 `Pro/` 前缀 |
| 实名 | **必须**，否则 403 |
| 赠金 | 新用户 2000 万 tokens（一次性，不要依赖） |

---

## 六、HTTP 状态码

| 状态码 | 原因 | 处理方案 |
|:------:|:-----|:---------|
| **200** | 正常 | ✅ |
| **400** | 参数非法 | 检查参数 |
| **401** | Key 错误 | 检查 `keys.json` |
| **403** | 未实名 / 余额不足 | 完成实名认证 |
| **429** | RPM/TPM 超限 | 增加间隔 |
| **30001** | 余额不足 | 实名或充值 |

---

## 七、注意事项

- ✅ **国内直连**，无需代理
- ✅ **永久免费模型池**：9B 以下，无限期
- ✅ **无 RPD 上限**（仅 RPM/TPM 滚动限流）
- ❌ **必须实名**（大陆手机号 + 身份证）
- ⚠️ **区分免费 vs 收费**：`Pro/` 前缀的是收费版
- ⚠️ 新用户 2000 万赠金用完即止，目标用永久免费模型

---

## 八、接入清单

- [x] 获取 API Key ✅
- [x] 记录到 `keys.json` ✅
- [x] 查可用模型 ✅ **93 个**
- [ ] **完成实名认证**（控制台 → 个人实名）
- [ ] 验证对话推理（实名后测试）
- [ ] 验证 `x-ratelimit-*` 响应头
- [ ] 集成到 `check-all.py`
