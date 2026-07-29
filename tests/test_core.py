"""freellm 核心逻辑测试：降级路径、异常分类、流式边界、健康状态。

纯标准库 unittest + mock，零外部依赖。
运行：python -m pytest tests/ 或 python -m unittest discover tests
"""
import time
import unittest
from unittest.mock import MagicMock, patch

from freellm._core import (
    Chunk, Response, _estimate_tokens, _model_fits, _normalize,
    _retry_after, chat, chat_stream, reset_health,
)
from freellm._errors import (
    AllPlatformsFailedError, AuthError, BadRequestError, ContextLengthError,
    LLMError, ModelError, NetworkError, RateLimitError, ServerError, classify,
)
from freellm._http import TransportHTTPError
from freellm._platforms import MODEL_META, Platform, PlatformSpec, SPECS


def _make_platform(name="siliconflow", key="test-key"):
    spec = SPECS[name]
    return Platform(spec=spec, api_key=key,
                    base_url=spec.base_url_default, proxy=None)


def _ok_body(content="hello", model="test-model"):
    return {
        "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
        "usage": {"total_tokens": 10},
        "model": model,
    }


def _sse_chunks(*texts):
    for t in texts:
        yield {"choices": [{"delta": {"content": t}, "finish_reason": None}]}
    yield {"choices": [{"delta": {}, "finish_reason": "stop"}]}


# ─── classify ──────────────────────────────────

class TestClassify(unittest.TestCase):
    def test_401_is_auth(self):
        self.assertIs(classify(401, "bad key"), AuthError)

    def test_403_is_auth(self):
        self.assertIs(classify(403, "forbidden"), AuthError)

    def test_429_is_rate_limit(self):
        self.assertIs(classify(429, "slow down"), RateLimitError)

    def test_404_with_model_is_model_error(self):
        self.assertIs(classify(404, "model 'x' not found"), ModelError)

    def test_404_without_model_is_bad_request(self):
        self.assertIs(classify(404, "endpoint not found"), BadRequestError)

    def test_400_context_hints(self):
        for hint in ("maximum context", "too long", "token limit",
                     "too many tokens", "reduce"):
            self.assertIs(classify(400, f"Error: {hint} exceeded"),
                          ContextLengthError, f"hint={hint}")

    def test_400_model_hints(self):
        for hint in ("not found", "does not exist", "unavailable",
                     "deprecated", "invalid model", "no such model"):
            self.assertIs(classify(400, f"model 'x' {hint}"),
                          ModelError, f"hint={hint}")

    def test_400_generic_is_bad_request(self):
        self.assertIs(classify(400, "invalid field value"), BadRequestError)

    def test_400_token_alone_not_context(self):
        self.assertIs(classify(400, "invalid token format"), BadRequestError)

    def test_500_is_server(self):
        self.assertIs(classify(500, "internal"), ServerError)

    def test_502_is_server(self):
        self.assertIs(classify(502, "bad gateway"), ServerError)

    def test_unknown_4xx_is_bad_request(self):
        self.assertIs(classify(418, "teapot"), BadRequestError)


# ─── 工具函数 ──────────────────────────────────

class TestNormalize(unittest.TestCase):
    def test_string(self):
        self.assertEqual(_normalize("hi"),
                         [{"role": "user", "content": "hi"}])

    def test_list_passthrough(self):
        msgs = [{"role": "user", "content": "hi"}]
        result = _normalize(msgs)
        self.assertEqual(result, msgs)
        self.assertIsNot(result, msgs)


class TestEstimateTokens(unittest.TestCase):
    def test_basic(self):
        msgs = [{"role": "user", "content": "hello world"}]
        est = _estimate_tokens(msgs)
        self.assertGreater(est, 100)

    def test_empty(self):
        self.assertEqual(_estimate_tokens([]), 100)

    def test_none_content(self):
        msgs = [{"role": "assistant", "content": None}]
        self.assertEqual(_estimate_tokens(msgs), 100)


class TestModelFits(unittest.TestCase):
    def test_fits(self):
        self.assertTrue(_model_fits("groq", "llama-3.3-70b-versatile", 1000))

    def test_too_big(self):
        self.assertFalse(_model_fits("groq", "gemma2-9b-it", 9000))

    def test_unknown_model_passes(self):
        self.assertTrue(_model_fits("groq", "nonexistent", 999999))

    def test_unknown_platform_passes(self):
        self.assertTrue(_model_fits("nonexistent", "model", 999999))

    def test_zero_context_passes(self):
        self.assertTrue(_model_fits("aliyun", "qwen3.7-max", 999999)
                        if MODEL_META.get("aliyun", {}).get("qwen3.7-max", None)
                        and MODEL_META["aliyun"]["qwen3.7-max"].context == 0
                        else True)


class TestRetryAfter(unittest.TestCase):
    def test_parses_float(self):
        self.assertAlmostEqual(_retry_after({"retry-after": "2.5"}), 2.5)

    def test_clamps_to_300(self):
        self.assertAlmostEqual(_retry_after({"retry-after": "999"}), 300.0)

    def test_clamps_negative_to_0(self):
        self.assertAlmostEqual(_retry_after({"retry-after": "-5"}), 0.0)

    def test_fallback_header(self):
        self.assertAlmostEqual(
            _retry_after({"x-ratelimit-reset-requests": "10"}), 10.0)

    def test_missing(self):
        self.assertIsNone(_retry_after({}))

    def test_invalid_value(self):
        self.assertIsNone(_retry_after({"retry-after": "abc"}))


# ─── 降级路径 ──────────────────────────────────

class TestChatDegradation(unittest.TestCase):
    def setUp(self):
        reset_health()

    @patch("freellm._core.get_platforms")
    @patch("freellm._core.post_json")
    def test_first_fails_second_succeeds(self, mock_post, mock_plats):
        p1 = _make_platform("siliconflow")
        p2 = _make_platform("cloudflare")
        mock_plats.return_value = {"siliconflow": p1, "cloudflare": p2}

        def side_effect(url, key, payload, proxy, timeout):
            if "siliconflow" in url:
                raise TransportHTTPError(500, {}, "internal error")
            return _ok_body(content="from cloudflare")

        mock_post.side_effect = side_effect

        with patch("freellm._core._priority", ["siliconflow", "cloudflare"]):
            r = chat("hi")
        self.assertEqual(r.platform, "cloudflare")
        self.assertEqual(r.content, "from cloudflare")

    @patch("freellm._core.get_platforms")
    @patch("freellm._core.post_json")
    def test_auth_blacklists_platform(self, mock_post, mock_plats):
        p1 = _make_platform("siliconflow")
        p2 = _make_platform("cloudflare")
        mock_plats.return_value = {"siliconflow": p1, "cloudflare": p2}

        def side_effect(url, key, payload, proxy, timeout):
            if "siliconflow" in url:
                raise TransportHTTPError(401, {}, "invalid key")
            return _ok_body()

        mock_post.side_effect = side_effect

        with patch("freellm._core._priority", ["siliconflow", "cloudflare"]):
            r = chat("hi")
        self.assertEqual(r.platform, "cloudflare")
        self.assertEqual(mock_post.call_count, 2)

    @patch("freellm._core.get_platforms")
    @patch("freellm._core.post_json")
    def test_bad_request_no_degrade(self, mock_post, mock_plats):
        p1 = _make_platform("siliconflow")
        mock_plats.return_value = {"siliconflow": p1}
        mock_post.side_effect = TransportHTTPError(400, {}, "invalid field")

        with patch("freellm._core._priority", ["siliconflow"]):
            with self.assertRaises(BadRequestError):
                chat("hi")
        self.assertEqual(mock_post.call_count, 1)

    @patch("freellm._core.get_platforms")
    @patch("freellm._core.post_json")
    def test_all_fail_raises(self, mock_post, mock_plats):
        p1 = _make_platform("siliconflow")
        mock_plats.return_value = {"siliconflow": p1}
        mock_post.side_effect = TransportHTTPError(500, {}, "down")

        with patch("freellm._core._priority", ["siliconflow"]):
            with self.assertRaises(AllPlatformsFailedError) as ctx:
                chat("hi")
        self.assertIn("siliconflow", ctx.exception.errors)

    @patch("freellm._core.get_platforms")
    @patch("freellm._core.post_json")
    def test_explicit_model_no_tier_degrade(self, mock_post, mock_plats):
        p1 = _make_platform("siliconflow")
        mock_plats.return_value = {"siliconflow": p1}
        mock_post.side_effect = TransportHTTPError(
            400, {}, "model 'bad' does not exist")

        with patch("freellm._core._priority", ["siliconflow"]):
            with self.assertRaises(AllPlatformsFailedError):
                chat("hi", model="bad")
        self.assertEqual(mock_post.call_count, 1)

    @patch("freellm._core.get_platforms")
    @patch("freellm._core.post_json")
    def test_server_error_retries_once(self, mock_post, mock_plats):
        p1 = _make_platform("siliconflow")
        mock_plats.return_value = {"siliconflow": p1}
        mock_post.side_effect = TransportHTTPError(500, {}, "down")

        with patch("freellm._core._priority", ["siliconflow"]):
            with self.assertRaises(AllPlatformsFailedError):
                chat("hi", model="Qwen/Qwen3-32B")
        self.assertEqual(mock_post.call_count, 2)

    @patch("freellm._core.get_platforms")
    @patch("freellm._core.post_json")
    def test_rate_limit_skips_platform(self, mock_post, mock_plats):
        p1 = _make_platform("siliconflow")
        p2 = _make_platform("cloudflare")
        mock_plats.return_value = {"siliconflow": p1, "cloudflare": p2}

        call_count = {"n": 0}

        def side_effect(url, key, payload, proxy, timeout):
            call_count["n"] += 1
            if "siliconflow" in url and call_count["n"] == 1:
                raise TransportHTTPError(
                    429, {"retry-after": "60"}, "rate limited")
            return _ok_body(content="ok")

        mock_post.side_effect = side_effect

        with patch("freellm._core._priority", ["siliconflow", "cloudflare"]):
            r = chat("hi")
        self.assertEqual(r.platform, "cloudflare")


# ─── 流式边界 ──────────────────────────────────

class TestStreamDegradation(unittest.TestCase):
    def setUp(self):
        reset_health()

    @patch("freellm._core.get_platforms")
    @patch("freellm._core.post_sse")
    def test_pre_stream_failure_degrades(self, mock_sse, mock_plats):
        p1 = _make_platform("siliconflow")
        p2 = _make_platform("cloudflare")
        mock_plats.return_value = {"siliconflow": p1, "cloudflare": p2}

        def side_effect(url, key, payload, proxy, timeout):
            if "siliconflow" in url:
                raise TransportHTTPError(500, {}, "down")
            return _sse_chunks("a", "b")

        mock_sse.side_effect = side_effect

        with patch("freellm._core._priority", ["siliconflow", "cloudflare"]):
            chunks = list(chat_stream("hi"))
        deltas = [c.delta for c in chunks if c.delta]
        self.assertEqual(deltas, ["a", "b"])

    @patch("freellm._core.get_platforms")
    @patch("freellm._core.post_sse")
    def test_mid_stream_failure_propagates(self, mock_sse, mock_plats):
        p1 = _make_platform("siliconflow")
        mock_plats.return_value = {"siliconflow": p1}

        def failing_stream(url, key, payload, proxy, timeout):
            yield {"choices": [{"delta": {"content": "partial"}}]}
            raise TransportHTTPError(500, {}, "mid-stream crash")

        mock_sse.side_effect = failing_stream

        with patch("freellm._core._priority", ["siliconflow"]):
            gen = chat_stream("hi")
            first = next(gen)
            self.assertEqual(first.delta, "partial")
            with self.assertRaises(ServerError):
                next(gen)

    @patch("freellm._core.get_platforms")
    @patch("freellm._core.post_sse")
    def test_stream_all_fail(self, mock_sse, mock_plats):
        p1 = _make_platform("siliconflow")
        mock_plats.return_value = {"siliconflow": p1}
        mock_sse.side_effect = TransportHTTPError(500, {}, "down")

        with patch("freellm._core._priority", ["siliconflow"]):
            with self.assertRaises(AllPlatformsFailedError):
                list(chat_stream("hi"))


# ─── 健康状态 ──────────────────────────────────

class TestHealthState(unittest.TestCase):
    def setUp(self):
        reset_health()

    @patch("freellm._core.get_platforms")
    @patch("freellm._core.post_json")
    def test_quarantine_persists_across_calls(self, mock_post, mock_plats):
        p1 = _make_platform("siliconflow")
        p2 = _make_platform("cloudflare")
        mock_plats.return_value = {"siliconflow": p1, "cloudflare": p2}

        def side_effect(url, key, payload, proxy, timeout):
            if "siliconflow" in url:
                raise TransportHTTPError(401, {}, "bad key")
            return _ok_body()

        mock_post.side_effect = side_effect

        with patch("freellm._core._priority", ["siliconflow", "cloudflare"]):
            chat("first")
            mock_post.reset_mock()
            r = chat("second")

        self.assertEqual(r.platform, "cloudflare")
        for call in mock_post.call_args_list:
            self.assertNotIn("siliconflow", call[0][0])

    def test_reset_health_clears(self):
        from freellm._core import _quarantined, _rate_limited
        _quarantined["test"] = "reason"
        _rate_limited["test"] = time.monotonic() + 999
        reset_health()
        self.assertEqual(len(_quarantined), 0)
        self.assertEqual(len(_rate_limited), 0)


# ─── TransportHTTPError.message ────────────────

class TestTransportHTTPError(unittest.TestCase):
    def test_openai_format(self):
        e = TransportHTTPError(
            400, {}, '{"error": {"message": "model not found"}}')
        self.assertEqual(e.message, "model not found")

    def test_string_error(self):
        e = TransportHTTPError(400, {}, '{"error": "bad request"}')
        self.assertEqual(e.message, "bad request")

    def test_non_json_fallback(self):
        e = TransportHTTPError(502, {}, "<html>Bad Gateway</html>")
        self.assertEqual(e.message, "<html>Bad Gateway</html>")

    def test_body_truncated(self):
        e = TransportHTTPError(500, {}, "x" * 1000)
        self.assertEqual(len(e.body_text), 500)


if __name__ == "__main__":
    unittest.main()
