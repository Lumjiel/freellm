"""平台声明 + 凭证加载 + 模型分层。

新增平台 = 往 SPECS 加一条 PlatformSpec + keys.json 加对应条目，其余模块零改动。
6 平台全部走 OpenAI 兼容 HTTP（含百炼 DashScope compatible-mode、Cloudflare /ai/v1）。

模型排序原则：SDK 不做智能排序。models 元组是出厂默认（按厂商命名惯例 + 参数量粗排），
用户通过 set_model_tiers() 覆盖。运行时根据 payload 长度自动排除上下文窗口不够的模型。
"""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ModelMeta:
    context: int = 0       # 上下文窗口（tokens），0 = 未知
    max_output: int = 0    # 最大输出（tokens），0 = 未知
    params: str = ""       # 参数量描述（"70B", "30B-A3B" 等），仅供展示


@dataclass(frozen=True)
class PlatformSpec:
    name: str                      # 规范名：platform= 参数 / keys.json 条目名
    key_field: str                 # keys.json 条目中的凭证字段名
    default_model: str             # chat 默认模型（= models[0]）
    base_url_default: str          # 可含 {字段} 占位符，用 keys 条目 format
    embed_model: str | None = None # embed 默认模型（None = 该平台不启用嵌入）
    models: tuple[str, ...] = ()   # 按质量降序的免费模型列表（出厂默认，可覆盖）


SPECS: dict[str, PlatformSpec] = {s.name: s for s in [
    PlatformSpec("groq", "key", "llama-3.3-70b-versatile",
                 "https://api.groq.com/openai/v1",
                 models=(
                     "llama-3.3-70b-versatile",
                     "deepseek-r1-distill-llama-70b",
                     "meta-llama/llama-4-scout-17b-16e-instruct",
                     "gemma2-9b-it",
                     "llama-3.1-8b-instant",
                 )),
    PlatformSpec("siliconflow", "key", "Qwen/Qwen3-32B",
                 "https://api.siliconflow.cn/v1",
                 embed_model="BAAI/bge-large-zh-v1.5",
                 models=(
                     "Qwen/Qwen3-32B",
                     "Qwen/Qwen3-14B",
                     "deepseek-ai/DeepSeek-V4-Flash",
                     "Qwen/Qwen3-8B",
                     "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
                     "THUDM/glm-4-9b-chat",
                     "Qwen/Qwen2.5-7B-Instruct",
                 )),
    PlatformSpec("cloudflare", "token", "@cf/meta/llama-3.3-70b-instruct",
                 "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
                 embed_model="@cf/baai/bge-large-en-v1.5",
                 models=(
                     "@cf/meta/llama-3.3-70b-instruct",
                     "@cf/deepseek-r1-distill-qwen-32b",
                     "@cf/qwen/qwen3-30b-a3b",
                     "@cf/meta/llama-4-scout-17b-16e-instruct",
                     "@cf/meta/llama-3.1-8b-instruct",
                     "@cf/meta/llama-3.2-3b-instruct",
                     "@cf/meta/llama-3.2-1b-instruct",
                 )),
    PlatformSpec("nvidia", "key", "meta/llama-3.1-70b-instruct",
                 "https://integrate.api.nvidia.com/v1",
                 models=(
                     "meta/llama-3.1-70b-instruct",
                     "deepseek-ai/deepseek-v4-pro",
                     "nvidia/nemotron-nano-30b",
                     "meta/llama-3.1-8b-instruct",
                     "nvidia/nemotron-nano-9b",
                 )),
    PlatformSpec("modelscope", "token_read", "Qwen/Qwen3.5-27B",
                 "https://api-inference.modelscope.cn/v1",
                 models=(
                     "Qwen/Qwen3-235B-A22B",
                     "Qwen/Qwen3.5-122B-A10B",
                     "deepseek-ai/DeepSeek-V4-Pro",
                     "Qwen/Qwen3.5-27B",
                     "Qwen/Qwen3-32B",
                     "Qwen/Qwen3-14B",
                     "Qwen/Qwen3-8B",
                 )),
    PlatformSpec("aliyun", "api_key", "qwen3.7-max",
                 "https://dashscope.aliyuncs.com/compatible-mode/v1",
                 models=(
                     "qwen3.7-max",
                     "qwen3.5-plus",
                     "qwen3.7-plus",
                     "deepseek-v4-pro",
                     "qwen3.6-27b",
                 )),
]}

DEFAULT_PRIORITY = ["siliconflow", "cloudflare", "nvidia", "modelscope", "aliyun", "groq"]

# ─── 模型元数据（上下文窗口 / 最大输出）────────────────────
# 0 = 未知（不做过滤）。数据来源：各平台文档，保守取值。
# 嵌套结构：platform → model → ModelMeta（避免同名模型跨平台冲突）

MODEL_META: dict[str, dict[str, ModelMeta]] = {
    "groq": {
        "llama-3.3-70b-versatile": ModelMeta(128000, 8192, "70B"),
        "deepseek-r1-distill-llama-70b": ModelMeta(128000, 8192, "70B"),
        "meta-llama/llama-4-scout-17b-16e-instruct": ModelMeta(128000, 8192, "17B-MoE"),
        "gemma2-9b-it": ModelMeta(8192, 8192, "9B"),
        "llama-3.1-8b-instant": ModelMeta(128000, 8192, "8B"),
    },
    "siliconflow": {
        "Qwen/Qwen3-32B": ModelMeta(32768, 8192, "32B"),
        "Qwen/Qwen3-14B": ModelMeta(32768, 8192, "14B"),
        "deepseek-ai/DeepSeek-V4-Flash": ModelMeta(32768, 8192, ""),
        "Qwen/Qwen3-8B": ModelMeta(32768, 8192, "8B"),
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B": ModelMeta(32768, 8192, "7B"),
        "THUDM/glm-4-9b-chat": ModelMeta(32768, 4096, "9B"),
        "Qwen/Qwen2.5-7B-Instruct": ModelMeta(32768, 8192, "7B"),
    },
    "cloudflare": {
        "@cf/meta/llama-3.3-70b-instruct": ModelMeta(8192, 2048, "70B"),
        "@cf/deepseek-r1-distill-qwen-32b": ModelMeta(8192, 2048, "32B"),
        "@cf/qwen/qwen3-30b-a3b": ModelMeta(8192, 2048, "30B-MoE"),
        "@cf/meta/llama-4-scout-17b-16e-instruct": ModelMeta(8192, 2048, "17B-MoE"),
        "@cf/meta/llama-3.1-8b-instruct": ModelMeta(8192, 2048, "8B"),
        "@cf/meta/llama-3.2-3b-instruct": ModelMeta(8192, 2048, "3B"),
        "@cf/meta/llama-3.2-1b-instruct": ModelMeta(8192, 2048, "1B"),
    },
    "nvidia": {
        "meta/llama-3.1-70b-instruct": ModelMeta(128000, 4096, "70B"),
        "deepseek-ai/deepseek-v4-pro": ModelMeta(128000, 4096, ""),
        "nvidia/nemotron-nano-30b": ModelMeta(128000, 4096, "30B"),
        "meta/llama-3.1-8b-instruct": ModelMeta(128000, 4096, "8B"),
        "nvidia/nemotron-nano-9b": ModelMeta(128000, 4096, "9B"),
    },
    "modelscope": {
        "Qwen/Qwen3-235B-A22B": ModelMeta(4096, 2048, "235B-MoE"),
        "Qwen/Qwen3.5-122B-A10B": ModelMeta(4096, 2048, "122B-MoE"),
        "deepseek-ai/DeepSeek-V4-Pro": ModelMeta(4096, 2048, ""),
        "Qwen/Qwen3.5-27B": ModelMeta(4096, 2048, "27B"),
        "Qwen/Qwen3-32B": ModelMeta(4096, 2048, "32B"),
        "Qwen/Qwen3-14B": ModelMeta(4096, 2048, "14B"),
        "Qwen/Qwen3-8B": ModelMeta(4096, 2048, "8B"),
    },
    "aliyun": {
        "qwen3.7-max": ModelMeta(32768, 8192, ""),
        "qwen3.5-plus": ModelMeta(131072, 8192, ""),
        "qwen3.7-plus": ModelMeta(131072, 8192, ""),
        "deepseek-v4-pro": ModelMeta(65536, 8192, ""),
        "qwen3.6-27b": ModelMeta(32768, 8192, "27B"),
    },
}

# ─── 用户覆盖的模型排序 ──────────────────────────

_model_overrides: dict[str, list[str]] = {}
_models_cache: dict[str, list[str]] = {}  # refresh_models() 写入的实时列表


def set_model_tiers(platform: str, models: list[str]) -> None:
    """覆盖某平台的模型优先级列表（按质量降序）。传空列表恢复出厂默认。"""
    if platform not in SPECS:
        raise ValueError(f"未知平台: {platform!r}，可选: {list(SPECS)}")
    if models:
        _model_overrides[platform] = list(models)
    else:
        _model_overrides.pop(platform, None)


def get_model_tiers(platform: str) -> list[str]:
    """获取某平台当前的模型优先级列表。优先级：用户覆盖 > 实时缓存 > 出厂默认。"""
    if platform in _model_overrides:
        return _model_overrides[platform]
    if platform in _models_cache:
        return _models_cache[platform]
    spec = SPECS[platform]
    return list(spec.models) if spec.models else [spec.default_model]


@dataclass
class Platform:
    """凭证解析后的可用平台。"""
    spec: PlatformSpec
    api_key: str
    base_url: str
    proxy: str | None


# ─── keys.json 加载 ──────────────────────────

_keys_cache: dict | None = None


def _find_keys_path() -> Path | None:
    """路径解析：FREELLM_KEYS 环境变量 > cwd/keys.json > 仓库根（包目录上级）。"""
    env = os.environ.get("FREELLM_KEYS")
    if env:
        return Path(env)
    cwd = Path.cwd() / "keys.json"
    if cwd.is_file():
        return cwd
    repo = Path(__file__).resolve().parent.parent / "keys.json"
    if repo.is_file():
        return repo
    return None


def _load_keys() -> dict:
    global _keys_cache
    if _keys_cache is not None:
        return _keys_cache
    path = _find_keys_path()
    if path is None:
        _keys_cache = {}
    else:
        with open(path, encoding="utf-8") as f:
            _keys_cache = json.load(f)
    return _keys_cache


def reload() -> None:
    """热加载：清空 keys 缓存，下次调用重新读盘。"""
    global _keys_cache
    _keys_cache = None


# ─── 凭证解析 ────────────────────────────────

def _resolve_credential(spec: PlatformSpec, entry: dict) -> str:
    key = str(entry.get(spec.key_field) or "")
    if key:
        return key
    if spec.name == "aliyun":
        # 百炼 fallback 链：bl CLI 的登录配置 → DASHSCOPE_API_KEY 环境变量
        try:
            cfg = json.loads(
                (Path.home() / ".bailian" / "config.json").read_text(encoding="utf-8"))
            if cfg.get("api_key"):
                return str(cfg["api_key"])
        except (OSError, json.JSONDecodeError):
            pass
        return os.environ.get("DASHSCOPE_API_KEY", "")
    return ""


def get_platforms() -> dict[str, Platform]:
    """当前可用平台（凭证解析成功且非空）。结果不缓存，每次反映 keys.json 现状。"""
    keys = _load_keys()
    out: dict[str, Platform] = {}
    for name, spec in SPECS.items():
        entry = keys.get(name) or {}
        api_key = _resolve_credential(spec, entry)
        if not api_key:
            continue
        try:
            base_url = str(entry.get("base_url") or spec.base_url_default.format(**entry))
        except KeyError:
            continue  # 占位符字段缺失（如 cloudflare 没配 account_id）
        out[name] = Platform(spec=spec, api_key=api_key,
                             base_url=base_url.rstrip("/"),
                             proxy=str(entry["proxy"]) if entry.get("proxy") else None)
    return out
