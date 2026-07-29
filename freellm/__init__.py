"""freellm — 最小 LLM 调用层：6 个免费平台互为备胎，零外部依赖。

    from freellm import chat, chat_stream, embed

    r = chat("用中文介绍量子计算")                     # 自动降级选平台
    r = chat("总结全文", platform="siliconflow")      # 指定平台（失败不降级）
    for c in chat_stream("数到 5"):                   # 流式
        print(c.delta, end="", flush=True)
    vec = embed("需要向量化的文本")                    # str → list[float]

    freellm.list_models()                             # 各平台模型优先级列表
    freellm.list_models(live=True)                    # 实时查询 /v1/models
    freellm.set_model_tiers("groq", ["llama-3.3-70b-versatile", ...])  # 覆盖排序

平台: groq / siliconflow / cloudflare / nvidia / modelscope / aliyun
环境变量: FREELLM_KEYS（keys.json 路径）、FREELLM_DEBUG=1（调试日志到 stderr）
"""
import logging
import os

from ._core import (Chunk, Response, chat, chat_stream, embed, list_models,
                    platforms, refresh_models, reset_health, set_priority)
from ._errors import (AllPlatformsFailedError, AuthError, BadRequestError,
                      ContextLengthError, LLMError, ModelError, NetworkError,
                      RateLimitError, ServerError)
from ._platforms import MODEL_META, ModelMeta, reload, set_model_tiers

__version__ = "0.2.0"

if os.environ.get("FREELLM_DEBUG"):
    logging.basicConfig(level=logging.DEBUG,
                        format="freellm %(levelname)s %(message)s")

__all__ = [
    "chat", "chat_stream", "embed", "platforms", "set_priority",
    "reset_health", "reload", "list_models", "refresh_models",
    "set_model_tiers", "MODEL_META", "ModelMeta",
    "Response", "Chunk",
    "LLMError", "AuthError", "RateLimitError", "ContextLengthError",
    "BadRequestError", "ServerError", "NetworkError", "ModelError",
    "AllPlatformsFailedError",
    "__version__",
]
