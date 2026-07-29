#!/usr/bin/env python3
"""check-all: 一键查询所有平台免费额度 + 写入用量台账"""
import json, subprocess, os
from datetime import datetime

KEYS = json.load(open("keys.json"))
LOG_FILE = "usage-log.md"

def curl_post(url, token, data_json, proxy=None):
    cmd = ["curl", "-s", "-D", "-", url,
           "-H", f"Authorization: Bearer {token}",
           "-H", "Content-Type: application/json",
           "-d", json.dumps(data_json)]
    if proxy:
        cmd = ["curl", "-s", "--proxy", proxy, "-D", "-", url,
               "-H", f"Authorization: Bearer {token}",
               "-H", "Content-Type: application/json",
               "-d", json.dumps(data_json)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        out = r.stdout.replace("\r\n", "\n")
        idx = out.rfind("\n\n")
        hdr_text = out[:idx] if idx >= 0 else out
        body_raw = out[idx+2:] if idx >= 0 else ""
        last_http = hdr_text.rfind("HTTP/")
        if last_http >= 0:
            hdr_text = hdr_text[last_http:]
        code = 0
        headers = {}
        for line in hdr_text.split("\n"):
            if line.startswith("HTTP/"):
                try: code = int(line.split(" ")[1])
                except: pass
            elif ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()
        try:
            body = json.loads(body_raw) if body_raw.strip() else {}
        except:
            body = body_raw[:200]
        return code, headers, body
    except subprocess.TimeoutExpired:
        return 0, {}, {"error": "timeout"}
    except Exception as e:
        return 0, {}, {"error": str(e)}    

date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
today = datetime.now().strftime("%Y-%m-%d")
print("=" * 52)
print(f"  多平台免费额度一键查询")
print(f"  {date_str}")
print("=" * 52)

# 收集结果用于台账
log_rows = []
log_ok = 0; log_total = 0

def check(name, status, detail=""):
    global log_ok, log_total
    log_total += 1
    if status == "ok": log_ok += 1
    icon = "✅" if status == "ok" else "⚠️" if status == "warn" else "❌"
    log_rows.append(f"| **{name}** | {icon} | {detail} |")

def heading(text):
    print(f"\n--- {text} ---")

def ok(text):
    print(f"  {text}")

# ─── 阿里百炼 ───────────────────────────────
heading("阿里云百炼")
bl_cmd = "bl.cmd" if os.name == "nt" else "bl"
summary = "err"
try:
    r = subprocess.run([bl_cmd, "usage", "free", "--expiring", "30", "--sort", "expires"],
                      capture_output=True, text=True, timeout=15)
    if r.returncode == 0:
        models = json.loads(r.stdout)
        urgent = [m for m in models if "2026-07-2" in m.get("expires", "")]
        detail = f"{len(urgent)} 个即将到期"
        log_ok += 1
        for m in models:
            e = m.get("expires", "")
            remain = m.get("remaining", 0)
            model = m.get("model", "")
            pct = m.get("usagePercent", 0)
            flag = "🔴" if "2026-07-2" in e else "🟡" if "2026-08" in e else "🟢"
            print(f"  {flag} {model}: {remain:,} ({e}) [{pct}%]")
    else:
        detail = "need login"
except FileNotFoundError:
    detail = "bl not installed"
except Exception as e:
    detail = str(e)
check("阿里百炼", "ok" if log_rows and not detail.startswith("need") else "warn", detail)

# ─── NVIDIA ──────────────────────────────────
heading("NVIDIA NIM")
nv = KEYS.get("nvidia", {})
nv_key = nv.get("key", "")
if nv_key:
    code, _, _ = curl_post("https://integrate.api.nvidia.com/v1/chat/completions",
        nv_key, {"model": "meta/llama-3.1-8b-instruct", "messages": [{"role":"user","content":"hi"}], "max_tokens": 1})
    status = code == 200
    ok(f"API: {'OK (200)' if status else f'HTTP {code}'}")
    check("NVIDIA", "ok" if status else "warn", f"{'OK' if status else f'HTTP {code}'}")
else:
    ok("Key not configured"); check("NVIDIA", "warn", "no key")

# ─── Cloudflare ──────────────────────────────
heading("Cloudflare Workers AI")
cf = KEYS.get("cloudflare", {})
cf_token = cf.get("token", "")
cf_account = cf.get("account_id", "")
if cf_token and cf_account:
    url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/run/@cf/meta/llama-3.2-1b-instruct"
    code, _, body = curl_post(url, cf_token,
        {"messages": [{"role":"user","content":"hi"}], "max_tokens": 1})
    if code == 200 and isinstance(body, dict) and body.get("success"):
        n = body["result"]["usage"]["neurons"]
        ok(f"API: OK | {n:.4f} Neurons | ~{int(10000/n):,}/day")
        check("Cloudflare", "ok", f"{n:.4f} Neurons")
    else:
        ok(f"API: HTTP {code}")
        check("Cloudflare", "warn", f"HTTP {code}")
else:
    ok("Config incomplete"); check("Cloudflare", "warn", "no config")

# ─── Groq ────────────────────────────────────
heading("Groq Cloud")
gq = KEYS.get("groq", {})
gq_key = gq.get("key", "")
gq_base = gq.get("base_url", "https://api.groq.com/openai/v1")
gq_proxy = gq.get("proxy", "")
if gq_key:
    code, headers, body = curl_post(f"{gq_base}/chat/completions", gq_key,
        {"model": "llama-3.1-8b-instant", "messages": [{"role":"user","content":"hi"}], "max_tokens": 1},
        proxy=gq_proxy or None)
    status = code == 200
    proxy_info = f" (proxy: {gq_proxy})" if gq_proxy else ""
    ok(f"API: {'OK (200)' if status else f'HTTP {code}'}{proxy_info}")
    remain = ""
    for k, v in sorted(headers.items()):
        if "ratelimit" in k:
            name = k.replace("x-ratelimit-", "").replace("-", " ").title()
            print(f"    {name}: {v}")
            if "remaining-requests" in k:
                remain = v
    check("Groq", "ok" if status else "warn", f"{remain}/14400" if remain else f"{'OK' if status else f'HTTP {code}'}")
else:
    ok("Key not configured"); check("Groq", "warn", "no key")

# ─── SiliconFlow ─────────────────────────────
heading("SiliconFlow 硅基流动")
sf = KEYS.get("siliconflow", {})
sf_key = sf.get("key", "")
sf_base = sf.get("base_url", "https://api.siliconflow.cn/v1")
if sf_key:
    code, headers, body = curl_post(f"{sf_base}/chat/completions", sf_key,
        {"model": "Qwen/Qwen2.5-7B-Instruct", "messages": [{"role":"user","content":"hi"}], "max_tokens": 1})
    status = code == 200
    ok(f"API: {'OK (200)' if status else f'HTTP {code}'}")
    check("硅基流动", "ok" if status else "warn", "OK" if status else f"HTTP {code}")
else:
    ok("Key not configured"); check("硅基流动", "warn", "no key")

# ─── ModelScope ──────────────────────────────
heading("ModelScope 魔搭")
ms = KEYS.get("modelscope", {})
ms_token = ms.get("token_read", "")
ms_base = ms.get("inference_base", "https://api-inference.modelscope.cn/v1")
if ms_token:
    code, headers, body = curl_post(f"{ms_base}/chat/completions", ms_token,
        {"model": "Qwen/Qwen3.5-27B", "messages": [{"role":"user","content":"hi"}], "max_tokens": 1})
    remain = ""
    for k, v in sorted(headers.items()):
        if "modelscope-ratelimit" in k:
            label = k.replace("modelscope-ratelimit-", "").replace("-", " ").title()
            print(f"  {label}: {v}")
            if "requests-remaining" in k:
                remain = v
    status = code == 200 or "requests-remaining" in str(headers)
    ok(f"API: {'OK' if code == 200 else f'HTTP {code}'}")
    check("ModelScope", "ok" if status else "warn", f"{remain}/2000" if remain else f"{'OK' if status else f'HTTP {code}'}")
else:
    ok("Token not configured"); check("ModelScope", "warn", "no token")

print()
print("=" * 52)
print(f"  查询完毕 ({log_ok}/{log_total} OK)")
print("=" * 52)

# ─── 写入用量台账 ────────────────────────────
log_entry = f"""\n## {today}\n
| 平台 | 状态 | 额度 |
|:----|:---:|:-----|
""" + "\n".join(log_rows) + "\n"

# 追加到日志文件
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
else:
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("# 用量台账\n\n每日各平台额度记录，由 `check-all.py` 自动写入。\n")
        f.write(log_entry)

print(f"\n📝 已记录到 {LOG_FILE}")
