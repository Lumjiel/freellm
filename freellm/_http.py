"""传输层：urllib.request POST JSON + SSE 流式。零外部依赖。

两条铁律：
1. 永远用显式 opener —— 有 proxy 走指定代理；无 proxy 用 ProxyHandler({})
   强制直连，防止 Clash 环境/系统代理劫持国内平台。
2. 传输层不做业务决策 —— 非 2xx 抛 TransportHTTPError 交上层 classify()；
   连接级失败包成 NetworkError。
"""
import json
import urllib.error
import urllib.request
from typing import Iterator

from ._errors import NetworkError


class TransportHTTPError(Exception):
    """HTTP 响应非 2xx，携带状态码、响应头（小写键）、错误消息。"""

    def __init__(self, status: int, headers: dict[str, str], body_text: str):
        self.status = status
        self.headers = headers
        self.body_text = body_text[:500]
        super().__init__(f"HTTP {status}: {self.message}")

    @property
    def message(self) -> str:
        """提取 OpenAI 标准错误消息（{"error": {"message": ...}}），失败退回原始文本。"""
        try:
            err = json.loads(self.body_text).get("error", {})
            if isinstance(err, dict) and err.get("message"):
                return str(err["message"])
            if isinstance(err, str) and err:
                return err
        except (json.JSONDecodeError, AttributeError, ValueError):
            pass
        return self.body_text


def _opener(proxy: str | None) -> urllib.request.OpenerDirector:
    if proxy:
        handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    else:
        # 空 dict = 无视环境/系统代理，强制直连
        handler = urllib.request.ProxyHandler({})
    return urllib.request.build_opener(handler)


def _open(url: str, api_key: str, payload: dict, proxy: str | None,
          timeout: int) -> urllib.request.addinfourl:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept-Encoding": "identity",  # 禁止 gzip，SSE 流才能逐行直读
    })
    try:
        return _opener(proxy).open(req, timeout=timeout)
    except urllib.error.HTTPError as e:  # 必须在 URLError 前捕获（HTTPError 是其子类）
        headers = {k.lower(): v for k, v in (e.headers or {}).items()}
        body = e.read().decode("utf-8", errors="replace")
        raise TransportHTTPError(e.code, headers, body) from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise NetworkError(f"连接失败: {getattr(e, 'reason', None) or e}") from None


def post_json(url: str, api_key: str, payload: dict, proxy: str | None = None,
              timeout: int = 60) -> dict:
    """POST JSON 并返回解析后的响应体。非 2xx 抛 TransportHTTPError，连接失败抛 NetworkError。"""
    with _open(url, api_key, payload, proxy, timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw[:500]}


def get_json(url: str, api_key: str, proxy: str | None = None,
             timeout: int = 30) -> dict:
    """GET 请求并返回 JSON。用于 /models 等查询端点。"""
    req = urllib.request.Request(url, method="GET", headers={
        "Authorization": f"Bearer {api_key}",
        "Accept-Encoding": "identity",
    })
    try:
        with _opener(proxy).open(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        headers = {k.lower(): v for k, v in (e.headers or {}).items()}
        body = e.read().decode("utf-8", errors="replace")
        raise TransportHTTPError(e.code, headers, body) from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise NetworkError(f"连接失败: {getattr(e, 'reason', None) or e}") from None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw[:500]}


def post_sse(url: str, api_key: str, payload: dict, proxy: str | None = None,
             timeout: int = 180) -> Iterator[dict]:
    """POST 流式请求（自动注入 stream=True），逐行解析 SSE，yield 每个 chunk 的 JSON。

    容错：忽略空行与 ':' 注释行；单行 JSON 解析失败跳过不中断；
    遇到 [DONE] 结束。流中断/连接错误由调用方处理。
    """
    resp = _open(url, api_key, {**payload, "stream": True}, proxy, timeout)
    try:
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or line.startswith(":") or not line.startswith("data:"):
                continue
            data = line[len("data:"):].strip()
            if data == "[DONE]":
                break
            try:
                yield json.loads(data)
            except json.JSONDecodeError:
                continue
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise NetworkError(f"流中断: {getattr(e, 'reason', None) or e}") from None
    finally:
        resp.close()
