# ModelScope 魔搭社区（推理 API）

> 更新时间：2026-07-21
> **API 基础地址**：`https://api-inference.modelscope.cn/v1`
> 鉴权：`Authorization: Bearer <ACCESS_TOKEN>`
> 额度：通过请求响应头 `modelscope-ratelimit-*` 读取
> 已记录到 `keys.json`

---

## 一、凭证

| 变量 | 值 |
|:-----|:----|
| `MODELSCOPE_ACCESS_TOKEN` | `ms-78709e6e...8adb`（只读） |
| `MODELSCOPE_WRITE_TOKEN` | `ms-5777345a...d78c`（写入） |
| `MODELSCOPE_INFERENCE_BASE` | `https://api-inference.modelscope.cn/v1` |
| `MODELSCOPE_OPENAPI_BASE` | `https://modelscope.cn/openapi/v1` |

---

## 二、可用模型（51 个）

> 完整列表：`curl -s "$MODELSCOPE_INFERENCE_BASE/models" -H "Authorization: Bearer $TOKEN"`

### 🔥 重点推荐

| 模型 ID | 说明 |
|:--------|:------|
| `Qwen/Qwen3-4B` | 通义千问轻量版 |
| `Qwen/Qwen3-8B` | 通义千问 8B |
| `Qwen/Qwen3-14B` | 通义千问 14B |
| `Qwen/Qwen3-32B` | 通义千问 32B |
| `Qwen/Qwen3-30B-A3B` | 通义 MoE 高效版 |
| `Qwen/Qwen3-235B-A22B` | 通义千问超大 MoE |
| `Qwen/Qwen3.5-27B` | ✅ 已验证可用 |
| `Qwen/Qwen3.5-35B-A3B` | 新版高效 |
| `Qwen/Qwen3.5-122B-A10B` | 新版大参数 |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | 代码专用 |
| `Qwen/Qwen3-VL-8B-Instruct` | 视觉多模态 |
| `Qwen/Qwen3-Next-80B-A3B-Instruct` | 下一代模型 |
| `deepseek-ai/DeepSeek-V3.2` | DeepSeek V3 |
| `deepseek-ai/DeepSeek-V4-Flash` | DeepSeek 轻量 |
| `deepseek-ai/DeepSeek-V4-Pro` | DeepSeek 完整版 |
| `stepfun-ai/Step-3.5-Flash` | 阶跃星辰 |
| `stepfun-ai/Step-3.7-Flash` | 阶跃星辰新版 |
| `ZhipuAI/GLM-4.7-Flash` | 智谱轻量 |
| `ZhipuAI/GLM-5` | 智谱旗舰 |
| `ZhipuAI/GLM-5.1` | 智谱新版 |
| `ZhipuAI/GLM-5.2` | 智谱最新 |
| `MiniMax/MiniMax-M2.7` | MiniMax |
| `MiniMax/MiniMax-M3` | MiniMax 最新 |
| `moonshotai/Kimi-K2.5` | 月之暗面 Kimi |
| `mistralai/Mistral-Large-Instruct-2407` | Mistral 大模型 |
| `PaddlePaddle/ERNIE-4.5-21B-A3B-PT` | 百度文心 |
| `Tencent-Hunyuan/Hy3` | 腾讯混元 |
| `Shanghai_AI_Laboratory/Intern-S2-Preview` | 上海 AI Lab |

---

## 三、快速命令

### 查可用模型

```bash
curl -s "$MODELSCOPE_INFERENCE_BASE/models" \
  -H "Authorization: Bearer $MODELSCOPE_ACCESS_TOKEN"
```

### 查每日剩余额度（魔搭独有！）

```bash
curl -s "$MODELSCOPE_OPENAPI_BASE/user/quota" \
  -H "Authorization: Bearer $MODELSCOPE_ACCESS_TOKEN"
```

### 对话推理

```bash
curl "$MODELSCOPE_INFERENCE_BASE/chat/completions" \
  -H "Authorization: Bearer $MODELSCOPE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3.5-27B",
    "messages": [
      {"role": "system", "content": "简洁命令行助手"},
      {"role": "user", "content": "你好"}
    ],
    "max_tokens": 2048,
    "temperature": 0.7
  }'
```

### 向量嵌入

```bash
curl "$MODELSCOPE_INFERENCE_BASE/embeddings" \
  -H "Authorization: Bearer $MODELSCOPE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bge-large-zh-v1.5",
    "input": "需要向量化的文本"
  }'
```

---

## 四、查询剩余额度

无独立配额接口，从推理请求的响应头读取：

```bash
curl -sI "$MODELSCOPE_INFERENCE_BASE/chat/completions" \
  -H "Authorization: Bearer $MODELSCOPE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen3-4B","messages":[{"role":"user","content":"hi"}],"max_tokens":1}' \
  | grep -i "modelscope-ratelimit"
```

### 返回字段

| Header | 含义 |
|:-------|:------|
| `Modelscope-Ratelimit-Requests-Limit` | 每日总额上限（2000） |
| `Modelscope-Ratelimit-Requests-Remaining` | 今日剩余次数 |
| `Modelscope-Ratelimit-Model-Requests-Limit` | 当前模型日上限 |
| `Modelscope-Ratelimit-Model-Requests-Remaining` | 当前模型剩余次数 |

---

## 五、免费额度规则

| 项目 | 数值 |
|:-----|:-----:|
| API 文本推理 | **2000 次/天** |
| 单模型日上限 | 200-500 次/天 |
| 重置时间 | 自然日 0 点 |
| 魔粒（Notebook/生图） | **100/天**（实名+50） |
| RPM | **120** / 分钟 |
| 并发 | **3** 个 |
| 上下文 | **≤ 4096 tokens** |
| max_tokens | **≤ 2048** |

---

## 七、HTTP 状态码

| 状态码 | 原因 | 处理方案 |
|:------:|:-----|:---------|
| **200** | 正常 | ✅ |
| **400** | 上下文超 4K / 参数非法 | 截断输入，max_tokens≤2048 |
| **401** | Token 错误 / 已删除 | 检查 `keys.json` |
| **403** | 未实名 / 未绑定阿里云 | 完成阿里云实名 |
| **429** | RPM/并发超限 | 增加 1s 间隔 |
| 额度耗尽 | 返额度不足提示 | 等次日 0 点重置 |

---

## 八、合规 & 注意事项

| ✅ 允许 | ❌ 禁止 |
|:--------|:--------|
| 本地 CLI / Agent | 对外提供服务 / 商用 |
| 本地 RAG / 学习测试 | 批量数万条数据集 |
| 私人问答 | 多账号刷额度/卖 Token |

- **需要阿里云实名** — 否则 API 被拦截
- **国内直连** — 延迟低
- **高峰时段**（9-12点/19-23点）少量限流
- **无 SLA**
- ⚠️ **两套域名别搞混**：推理用 `api-inference.`，查额度用 `modelscope.cn/openapi`

---

## 九、接入清单

- [x] 获取 Access Token ✅
- [x] 记录到 `keys.json` ✅
- [x] 查可用模型 ✅ **51 个**
- [x] 验证推理 API ✅ `Qwen/Qwen3.5-27B` 可用
- [x] 验证额度查询 ✅（从 `modelscope-ratelimit-*` 响应头读取）
- [x] 集成到 `check-all.sh` ✅
