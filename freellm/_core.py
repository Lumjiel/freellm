"""调用核心：chat / chat_stream / embed + 降级控制器 + 进程内健康状态。

降级策略（自动模式，档位优先）：
- 外层按模型档位（tier）遍历：先试所有平台的最强模型，全挂再试第二档
- 内层按平台优先级遍历：同档位内按 _priority 顺序
- ModelError（模型不存在/下架）→ 同档位换下一个平台
- ContextLengthError → 同档位换下一个平台（别家窗口可能更大）
- AuthError 拉黑平台 / RateLimitError 记 reset 时间戳 / NetworkError 换下家
- BadRequestError（payload 本身问题）→ 直接上抛，不换平台
- ServerError 同平台重试一次（0.5s 退避）后再换
- 全部失败 → AllPlatformsFailedError（携带各平台错误）

显式 platform= 时不做平台降级，但仍走模型档位降级（除非同时指定了 model=）。
显式 model= 时不做任何降级。
"""
import logging
import time
from dataclasses import dataclass, field
from typing import Iterator

from ._errors import (
    AllPlatformsFailedError, AuthError, BadRequestError, ContextLengthError,
    LLMError, ModelError, RateLimitError, ServerError, classify,
)
from ._http import TransportHTTPError, post_json, post_sse
from ._platforms import (MODEL_META, SPECS, DEFAULT_PRIORITY, Platform,
                         _models_cache, get_model_tiers, get_platforms)

log = logging.getLogger("freellm")

# ─── 进程内健康状态 ──────────────────────────

_quarantined: dict[str, str] = {}     # 平台名 → 拉黑原因（AuthError，凭证坏了）
_rate_limited: dict[str, float] = {}  # 平台名 → 限流恢复时间戳（monotonic）


def reset_health() -> None:
    """清空拉黑/限流记录（长驻进程可定期调用，或测试用）。"""
    _quarantined.clear()
    _rate_limited.clear()


# ─── 返回结构 ────────────────────────────────

@dataclass
class Response:
    content: str
    platform: str
    model: str
    usage: dict = field(default_factory=dict)
    finish_reason: str | None = None


@dataclass
class Chunk:
    delta: str = ""
    finish_reason: str | None = None
    usage: dict | None = None


# ─── 优先级管理 ──────────────────────────────

_priority: list[str] = list(DEFAULT_PRIORITY)


def set_priority(names: list[str]) -> None:
    """调整自动降级的平台顺序（如百炼额度快到期时置顶先消耗）。"""
    unknown = [n for n in names if n not in SPECS]
    if unknown:
        raise ValueError(f"未知平台: {unknown}，可选: {list(SPECS)}")
    _priority[:] = list(names)


# ─── 内部工具 ────────────────────────────────

def _normalize(messages: str | list[dict]) -> list[dict]:
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]
    return list(messages)


def _estimate_tokens(msgs: list[dict]) -> int:
    """粗略估算消息列表的 token 数。中文约 1 字 = 1.5 token，英文约 4 字符 = 1 token。
    取 len * 0.75 作为中英混合的折中估算，+100 给格式开销。"""
    total = sum(len(m.get("content") or "") for m in msgs)
    return int(total * 0.75) + 100


def _model_fits(platform: str, model: str, est_tokens: int) -> bool:
    """检查模型上下文窗口是否能容纳估算的 token 数。未知窗口不过滤。"""
    meta = MODEL_META.get(platform, {}).get(model)
    if not meta or meta.context <= 0:
        return True
    return est_tokens < meta.context


def _candidates(platform: str | None, plats: dict[str, Platform]) -> list[str]:
    if platform:
        if platform not in plats:
            raise LLMError(
                f"平台 {platform!r} 不可用（凭证未配置或解析失败），"
                f"当前可用: {', '.join(plats) or '无'}")
        return [platform]
    now = time.monotonic()
    out = []
    for name in _priority:
        if name not in plats:
            continue
        if name in _quarantined:
            log.debug("跳过 %s（已拉黑: %s）", name, _quarantined[name])
            continue
        if _rate_limited.get(name, 0) > now:
            log.debug("跳过 %s（限流中，%.0fs 后恢复）", name,
                      _rate_limited[name] - now)
            continue
        out.append(name)
    return out


def _retry_after(headers: dict[str, str]) -> float | None:
    for h in ("retry-after", "x-ratelimit-reset-requests"):
        v = headers.get(h)
        if v:
            try:
                return min(max(float(v), 0), 300.0)
            except ValueError:
                pass
    return None


def _to_error(te: TransportHTTPError) -> LLMError:
    cls = classify(te.status, te.message)
    if cls is RateLimitError:
        return RateLimitError(te.message, status=te.status,
                              retry_after=_retry_after(te.headers))
    return cls(te.message, status=te.status)


def _record_health(name: str, e: LLMError) -> None:
    if isinstance(e, AuthError):
        _quarantined[name] = str(e)
    elif isinstance(e, RateLimitError):
        _rate_limited[name] = time.monotonic() + (e.retry_after or 30.0)


def _handle_failure(name: str, e: LLMError, explicit: bool,
                    errors: dict[str, LLMError]) -> None:
    """记录错误、更新健康状态；决定上抛（explicit / BadRequest）还是继续降级。"""
    e.platform = name
    errors[name] = e
    _record_health(name, e)
    log.warning("%s 失败: %s", name, e)
    if explicit or isinstance(e, BadRequestError):
        raise e


def _is_model_level(e: LLMError) -> bool:
    """判断是否为模型级错误（换模型即可，不判平台死刑）。"""
    return isinstance(e, (ModelError, ContextLengthError))


def _prepare(messages: str | list[dict], platform: str | None,
             model: str | None):
    """chat / chat_stream 共用前置：规范化消息、解析候选平台、构建模型档位列表。"""
    msgs = _normalize(messages)
    plats = get_platforms()
    names = _candidates(platform, plats)
    if not names:
        raise LLMError("无可用平台（检查 keys.json / 拉黑状态，或 reset_health()）")
    explicit_model = model is not None
    if explicit_model:
        model_lists = {n: [model] for n in names}
        max_depth = 1
    else:
        model_lists = {n: get_model_tiers(n) for n in names}
        max_depth = max(len(v) for v in model_lists.values())
    est_tokens = _estimate_tokens(msgs)
    return msgs, plats, names, explicit_model, model_lists, max_depth, est_tokens


def _iter_candidates(names: list[str], plats: dict[str, Platform],
                     model_lists: dict[str, list[str]], max_depth: int,
                     est_tokens: int, skipped: dict[str, str]):
    """按档位 × 平台优先级产出 (name, Platform, model)，跳过不健康/窗口不够的。"""
    for tier in range(max_depth):
        for name in names:
            if name in _quarantined:
                continue
            if _rate_limited.get(name, 0) > time.monotonic():
                continue
            tiers = model_lists[name]
            if tier >= len(tiers):
                continue
            mdl = tiers[tier]
            if not _model_fits(name, mdl, est_tokens):
                log.debug("跳过 %s/%s（上下文窗口不够，估算 %d tokens）",
                          name, mdl, est_tokens)
                skipped[f"{name}/{mdl}"] = "上下文窗口不够"
                continue
            yield name, plats[name], mdl


def _fail(errors: dict[str, LLMError], skipped: dict[str, str],
          est_tokens: int):
    """所有候选耗尽后的终结异常。"""
    if not errors and skipped:
        raise LLMError(
            f"所有模型上下文窗口不够（估算 {est_tokens} tokens）— "
            + "; ".join(f"{k}: {v}" for k, v in list(skipped.items())[:5]))
    raise AllPlatformsFailedError(errors)


# ─── chat ────────────────────────────────────

def _chat_payload(model: str, msgs: list[dict], temperature: float,
                  max_tokens: int, response_format: dict | None) -> dict:
    payload = {"model": model, "messages": msgs,
               "temperature": temperature, "max_tokens": max_tokens}
    if response_format is not None:
        payload["response_format"] = response_format
    return payload


def _do_chat(p: Platform, payload: dict, timeout: int) -> Response:
    body = post_json(f"{p.base_url}/chat/completions", p.api_key, payload,
                     p.proxy, timeout)
    if "_raw" in body:
        raise ServerError(f"响应非 JSON: {body['_raw'][:200]}",
                          platform=p.spec.name)
    choice = (body.get("choices") or [{}])[0]
    return Response(
        content=(choice.get("message") or {}).get("content") or "",
        platform=p.spec.name, model=payload["model"],
        usage=body.get("usage") or {},
        finish_reason=choice.get("finish_reason"))


def _attempt_chat(p: Platform, payload: dict, timeout: int) -> Response:
    """单平台调用：ServerError 同平台重试一次（0.5s），其余异常直接上抛。"""
    try:
        return _do_chat(p, payload, timeout)
    except TransportHTTPError as te:
        exc = _to_error(te)
        if not isinstance(exc, ServerError):
            raise exc from None
        log.debug("%s 5xx，0.5s 后重试", p.spec.name)
        time.sleep(0.5)
        try:
            return _do_chat(p, payload, timeout)
        except TransportHTTPError as te2:
            raise _to_error(te2) from None


def chat(messages: str | list[dict], *, platform: str | None = None,
         model: str | None = None, temperature: float = 0.7,
         max_tokens: int = 2048, timeout: int = 60,
         response_format: dict | None = None) -> Response:
    """统一对话接口。messages 可为字符串或多轮消息列表。

    自动模式：按模型档位 × 平台优先级降级；全部失败抛 AllPlatformsFailedError。
    显式 model=：只用该模型，不降级。
    显式 platform=（无 model=）：该平台内按档位降级。
    """
    msgs, plats, names, explicit_model, model_lists, max_depth, est_tokens = \
        _prepare(messages, platform, model)
    errors: dict[str, LLMError] = {}
    skipped: dict[str, str] = {}

    for name, p, mdl in _iter_candidates(names, plats, model_lists, max_depth,
                                         est_tokens, skipped):
        payload = _chat_payload(mdl, msgs, temperature, max_tokens,
                                response_format)
        log.debug("尝试 %s / %s", name, mdl)
        try:
            return _attempt_chat(p, payload, timeout)
        except LLMError as e:
            if _is_model_level(e) and not explicit_model:
                log.debug("%s/%s 模型级失败: %s", name, mdl, e)
                errors[f"{name}/{mdl}"] = e
                continue
            _handle_failure(name, e, platform is not None, errors)
            continue

    _fail(errors, skipped, est_tokens)


# ─── chat_stream ─────────────────────────────

def _to_chunk(raw: dict) -> Chunk:
    choice = (raw.get("choices") or [{}])[0]
    return Chunk(delta=(choice.get("delta") or {}).get("content") or "",
                 finish_reason=choice.get("finish_reason"),
                 usage=raw.get("usage"))


def _attempt_stream(p: Platform, payload: dict,
                    timeout: int) -> Iterator[Chunk]:
    try:
        for raw in post_sse(f"{p.base_url}/chat/completions", p.api_key,
                            payload, p.proxy, timeout):
            yield _to_chunk(raw)
    except TransportHTTPError as te:
        raise _to_error(te) from None


def chat_stream(messages: str | list[dict], *, platform: str | None = None,
                model: str | None = None, temperature: float = 0.7,
                max_tokens: int = 2048, timeout: int = 180,
                response_format: dict | None = None) -> Iterator[Chunk]:
    """流式对话，yield Chunk（delta 为增量文本）。

    降级只发生在产出第一个 chunk 之前；流一旦开始，中断异常直接透传给消费方。
    流式不做同平台 5xx 重试。
    """
    msgs, plats, names, explicit_model, model_lists, max_depth, est_tokens = \
        _prepare(messages, platform, model)
    errors: dict[str, LLMError] = {}
    skipped: dict[str, str] = {}

    for name, p, mdl in _iter_candidates(names, plats, model_lists, max_depth,
                                         est_tokens, skipped):
        payload = _chat_payload(mdl, msgs, temperature, max_tokens,
                                response_format)
        log.debug("流式尝试 %s / %s", name, mdl)
        produced = False
        try:
            for chunk in _attempt_stream(p, payload, timeout):
                produced = True
                yield chunk
            return
        except LLMError as e:
            if produced:
                e.platform = name
                raise
            if _is_model_level(e) and not explicit_model:
                log.debug("%s/%s 模型级失败: %s", name, mdl, e)
                errors[f"{name}/{mdl}"] = e
                continue
            _handle_failure(name, e, platform is not None, errors)
            continue

    _fail(errors, skipped, est_tokens)


# ─── embed ───────────────────────────────────

def embed(text: str | list[str], *, platform: str | None = None,
          model: str | None = None, timeout: int = 30):
    """文本向量化。str → list[float]；list[str] → list[list[float]]。

    自动模式只在支持嵌入的平台间降级（siliconflow / cloudflare）。
    """
    plats = get_platforms()
    names = _candidates(platform, plats)
    if not names:
        raise LLMError("无可用平台（检查 keys.json / 拉黑状态，或 reset_health()）")
    if platform and not model and not plats[platform].spec.embed_model:
        raise LLMError(f"平台 {platform!r} 无默认嵌入模型，请指定 model=")
    errors: dict[str, LLMError] = {}
    for name in names:
        p = plats[name]
        mdl = model or p.spec.embed_model
        if not mdl:
            continue
        log.debug("嵌入尝试 %s / %s", name, mdl)
        try:
            body = post_json(f"{p.base_url}/embeddings", p.api_key,
                             {"model": mdl, "input": text}, p.proxy, timeout)
            data = body.get("data") or []
            if not data:
                raise ServerError("嵌入响应缺少 data 字段", platform=name)
            vecs = [d.get("embedding") or [] for d in data]
            return vecs[0] if isinstance(text, str) else vecs
        except TransportHTTPError as te:
            _handle_failure(name, _to_error(te), platform is not None, errors)
        except LLMError as e:
            _handle_failure(name, e, platform is not None, errors)
    raise AllPlatformsFailedError(errors)


# ─── 模型查询 / 刷新 ─────────────────────────


def list_models(platform: str | None = None, *,
                live: bool = False) -> dict[str, list[str]]:
    """查询各平台可用模型。

    live=False（默认）：返回当前生效的模型优先级列表（静态 + 用户覆盖）。
    live=True：调 GET /v1/models 拿实时列表（不排序，按平台返回顺序）。
    """
    if live:
        return refresh_models(platform)
    plats = get_platforms()
    targets = [platform] if platform else list(SPECS)
    out: dict[str, list[str]] = {}
    for name in targets:
        if name not in SPECS:
            raise ValueError(f"未知平台: {name!r}，可选: {list(SPECS)}")
        out[name] = get_model_tiers(name)
    return out


def refresh_models(platform: str | None = None) -> dict[str, list[str]]:
    """从 GET /v1/models 拉取实时模型列表，更新进程内缓存。

    保留 curated 顺序：curated 列表中仍存在的模型保持原序，新发现的模型追加到末尾。
    缓存纯进程内，不持久化。
    """
    from ._http import get_json
    plats = get_platforms()
    targets = [platform] if platform else [n for n in _priority if n in plats]
    out: dict[str, list[str]] = {}
    for name in targets:
        p = plats.get(name)
        if not p:
            continue
        try:
            body = get_json(f"{p.base_url}/models", p.api_key, p.proxy, 15)
            live = {m["id"] for m in (body.get("data") or [])
                    if isinstance(m, dict) and m.get("id")}
            if not live:
                out[name] = get_model_tiers(name)
                continue
            spec = SPECS[name]
            curated = list(spec.models) if spec.models else [spec.default_model]
            ordered = [m for m in curated if m in live]
            ordered += [m for m in live if m not in curated]
            _models_cache[name] = ordered
            out[name] = ordered
        except Exception as e:
            log.warning("刷新 %s 模型列表失败: %s", name, e)
            out[name] = get_model_tiers(name)
    return out


# ─── 诊断 ────────────────────────────────────

def platforms() -> list[dict]:
    """各平台状态：可用性、模型列表、代理、拉黑/限流情况。"""
    now = time.monotonic()
    avail = get_platforms()
    out = []
    for name in _priority:
        p = avail.get(name)
        rl = _rate_limited.get(name, 0) - now
        out.append({
            "name": name,
            "available": p is not None,
            "models": (tiers := get_model_tiers(name)),
            "default_model": tiers[0],
            "proxy": bool(p and p.proxy),
            "embed": bool((p.spec if p else SPECS[name]).embed_model),
            "quarantined": _quarantined.get(name),
            "rate_limited_sec": round(rl, 1) if rl > 0 else None,
        })
    return out
