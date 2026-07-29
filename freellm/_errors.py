"""异常体系：HTTP 状态 / 网络错误 → 分类异常，供降级控制器决策。"""


class LLMError(Exception):
    """所有 freellm 异常的基类。"""

    def __init__(self, message: str, *, platform: str | None = None,
                 status: int | None = None):
        super().__init__(message)
        self.platform = platform    # 出错的平台名
        self.status = status        # HTTP 状态码（网络错误为 None）


class AuthError(LLMError):
    """401/403 — 凭证无效。平台被本进程拉黑，不再重试。"""


class RateLimitError(LLMError):
    """429 — 触发限流。retry_after 秒内跳过该平台。"""

    def __init__(self, message: str, *, platform=None, status=429,
                 retry_after: float | None = None):
        super().__init__(message, platform=platform, status=status)
        self.retry_after = retry_after


class ModelError(LLMError):
    """模型不存在/已下架/不可用 — 同档位换下一个平台的同档模型。"""


class ContextLengthError(LLMError):
    """400 且消息含上下文超长特征 — 换下一个模型/平台（别家窗口可能更大）。"""


class BadRequestError(LLMError):
    """其余 400 — payload 本身的问题，换平台也会失败，直接上抛。"""


class ServerError(LLMError):
    """5xx — 同平台重试一次，仍失败换下家。"""


class NetworkError(LLMError):
    """连接失败 / 超时 / DNS — 换下家。"""


class AllPlatformsFailedError(LLMError):
    """自动降级模式下所有平台都失败。errors 记录每个平台的失败原因。"""

    def __init__(self, errors: dict[str, LLMError]):
        self.errors = errors
        detail = "; ".join(f"{p}: {e}" for p, e in errors.items())
        super().__init__(f"所有平台不可用 — {detail}")


# ─── HTTP 响应分类 ───────────────────────────

_CONTEXT_HINTS = ("context", "too long", "maximum context", "max_tokens",
                  "reduce", "token limit", "too many tokens")

_MODEL_HINTS = ("not found", "does not exist", "unavailable",
                "deprecated", "invalid model", "no such model",
                "not supported", "has been removed")


def classify(status: int, message: str) -> type[LLMError]:
    """(HTTP 状态码, 错误消息) → 异常类。"""
    if status in (401, 403):
        return AuthError
    if status == 429:
        return RateLimitError
    if status == 404:
        low = message.lower()
        if "model" in low:
            return ModelError
        return BadRequestError
    if status == 400:
        low = message.lower()
        if any(h in low for h in _CONTEXT_HINTS):
            return ContextLengthError
        if "model" in low and any(h in low for h in _MODEL_HINTS):
            return ModelError
        return BadRequestError
    if status >= 500:
        return ServerError
    return BadRequestError
