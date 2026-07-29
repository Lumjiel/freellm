# Groq Cloud Free Tier

> 更新时间：2026-07-22（验证更新：403 Forbidden，key 失效）
> API Base：`https://api.groq.com/openai/v1`（OpenAI 标准兼容）
> 密钥前缀：`gsk_`
> 网络要求：🌐 **需要海外网络**（国内直连不通）
> 免费性质：永续速率限制免费层，LPU 硬件超高速推理（500~3000 token/s）

---

## 一、凭证

| 变量 | 值 | 状态 |
|:-----|:----|:----:|
| `GROQ_API_KEY` | `gsk_COa8RhrW...9Je` | ⚠️ 403 Forbidden（需重新生成） |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | ✅ |
| 网络连通 | 需代理（Clash 127.0.0.1:7897） | ✅ 已验证 |

---

## 二、可用模型

> 模型列表：`curl -s "$GROQ_BASE_URL/models" -H "Authorization: Bearer $GROQ_API_KEY"`

### 免费模型额度对照表

| 模型 ID | RPM | TPM | RPD | TPD |
|:--------|:---:|:---:|:---:|:---:|
| `llama-3.1-8b-instant` | 30 | 6,000 | **14,400** | 500,000 |
| `llama-3.3-70b-versatile` | 30 | 12,000 | 1,000 | 100,000 |
| `deepseek-r1-distill-llama-70b` | 30 | 12,000 | 1,000 | 100,000 |
| `meta-llama/llama-4-scout-17b-16e-instruct` | 30 | 30,000 | 1,000 | 500,000 |
| `gemma2-9b-it` | 30 | 15,000 | 1,000 | 500,000 |

### 推荐策略

| 用途 | 模型 | 理由 |
|:-----|:-----|:------|
| **日常批量** | `llama-3.1-8b-instant` | RPD 14400，最宽松 |
| **复杂推理** | `deepseek-r1-distill-llama-70b` | RPD 1000，按需用 |
| **轻量任务** | `gemma2-9b-it` | TPD 500,000 |

---

## 三、快速命令

### 查可用模型

```bash
curl -s "$GROQ_BASE_URL/models" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  | python -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data']]"
```

### 对话推理

```bash
curl "$GROQ_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.1-8b-instant",
    "messages": [
      {"role": "system", "content": "简洁命令行助手"},
      {"role": "user", "content": "你好"}
    ],
    "temperature": 0.7,
    "max_tokens": 1024
  }'
```

### 流式输出

```bash
curl "$GROQ_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "stream": true,
    "model": "llama-3.1-8b-instant",
    "messages": [{"role":"user","content":"hi"}]
  }'
```

---

## 四、查询剩余额度

无独立配额接口。从推理请求的响应头读取（和 NVIDIA 一致）：

```bash
curl -sI "$GROQ_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model":"llama-3.1-8b-instant",
    "messages":[{"role":"user","content":"hi"}],
    "max_tokens":1
  }' \
  | grep -E "x-ratelimit"
```

### 响应头字段

| Header | 含义 |
|:-------|:------|
| `x-ratelimit-limit-requests` | 当前模型 RPM 上限 |
| `x-ratelimit-remaining-requests` | 当前分钟剩余请求 |
| `x-ratelimit-reset-requests` | 限流多少秒后重置 |
| `x-ratelimit-limit-tokens` | 每分钟 TPM 上限 |
| `x-ratelimit-remaining-tokens` | 当前分钟剩余 Token |
| `x-ratelimit-reset-tokens` | Token 限流多少秒后重置 |

> ⚠️ **注意**：响应头不返回每日剩余请求（RPD），需要脚本本地自建计数器，UTC 零点清零。

---

## 五、免费额度规则

| 项目 | 数值 |
|:-----|:-----:|
| 注册门槛 | **邮箱 / GitHub，无需手机号/信用卡** |
| RPM | 30（所有免费模型） |
| 并发 | **≤ 3** |
| max_tokens | 最高 8192 |
| 上下文 | 8B = 128K, 70B = 128K |
| 重置 | UTC 0 点（北京时间 08:00） |
| 多 Key 翻倍 | ❌ 不叠加 |

---

## 六、HTTP 状态码

| 状态码 | 原因 | 处理方案 |
|:------:|:-----|:---------|
| **200** | 正常 | ✅ |
| **400** | 上下文超长 / 参数非法 | 截断输入，控制输出 |
| **401** | API Key 错误 / 已删除 | 重新复制 gsk_ 密钥 |
| **404** | model 名写错 | 执行模型列表核对 ID |
| **429** | RPM/TPM/RPD 超限 | 读 `x-ratelimit-reset`，等秒数重试 |
| **500/503** | 服务器过载 | 等待重试，换轻量模型 |

---

## 七、合规 & 注意事项

| ✅ 允许 | ❌ 禁止 |
|:--------|:--------|
| 本地 CLI / Agent | 对外提供服务 / 商用 |
| 本地 RAG / 学习测试 | 大规模批量离线推理 |
| 私人问答 | 多账号刷额度 / 卖 Key |

- 🌐 **需要海外网络**（代理）
- 🚀 **超高速推理**（500~3000 token/s）
- 📊 **本地计数器**：每日 RPD 需本地记录，UTC 0 点清零
- 💡 **优先策略**：Groq > 英伟达 > Cloudflare > 魔搭
- 🔄 不同模型额度独立，探测时需指定对应模型 ID

---

## 八、接入清单

- [x] 注册 Groq 账号
- [x] 生成 API Key
- [x] Key 已记录到 `keys.json`
- [x] **验证 API 连通性**（2026-07-22：报 `403 Forbidden`，代理连通但 key 被拒绝，需重新生成）
- [ ] 查可用模型列表
- [ ] 验证 `x-ratelimit-*` 响应头
- [ ] 集成到 `check-all.py`
