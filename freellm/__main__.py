"""CLI 入口：python -m freellm chat|embed|platforms|models（调试与管理用）。"""
import argparse
import sys

from . import (__version__, chat, chat_stream, embed, list_models, platforms,
               refresh_models)
from ._errors import LLMError


def _main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(prog="freellm",
                                 description="最小 LLM 调用层（6 免费平台互备）")
    ap.add_argument("--version", action="version", version=f"freellm {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("chat", help="对话（默认自动降级）")
    c.add_argument("prompt")
    c.add_argument("--platform", help="指定平台，失败不降级")
    c.add_argument("--model")
    c.add_argument("--stream", action="store_true", help="流式输出")
    c.add_argument("--temperature", type=float, default=0.7)
    c.add_argument("--max-tokens", type=int, default=2048)

    e = sub.add_parser("embed", help="文本向量化")
    e.add_argument("text")
    e.add_argument("--platform")
    e.add_argument("--model")

    sub.add_parser("platforms", help="各平台可用性 / 健康状态")

    m = sub.add_parser("models", help="各平台模型列表（按优先级）")
    m.add_argument("--platform", help="只看指定平台")
    m.add_argument("--live", action="store_true",
                   help="实时查询 /v1/models（而非静态列表）")

    args = ap.parse_args()
    try:
        if args.cmd == "chat":
            if args.stream:
                for chunk in chat_stream(args.prompt, platform=args.platform,
                                         model=args.model,
                                         temperature=args.temperature,
                                         max_tokens=args.max_tokens):
                    if chunk.delta:
                        print(chunk.delta, end="", flush=True)
                print()
            else:
                r = chat(args.prompt, platform=args.platform, model=args.model,
                         temperature=args.temperature,
                         max_tokens=args.max_tokens)
                print(r.content)
                tok = r.usage.get("total_tokens")
                tail = f" | {tok} tokens" if tok else ""
                print(f"\n[{r.platform} | {r.model}{tail}]", file=sys.stderr)
        elif args.cmd == "embed":
            vec = embed(args.text, platform=args.platform, model=args.model)
            print(f"维度: {len(vec)}  前 5 项: {vec[:5]}")
        elif args.cmd == "platforms":
            for p in platforms():
                icon = "✅" if p["available"] else "❌"
                extra = []
                if p["proxy"]:
                    extra.append("代理")
                if p["embed"]:
                    extra.append("嵌入")
                if p["quarantined"]:
                    extra.append(f"已拉黑: {p['quarantined']}")
                if p["rate_limited_sec"]:
                    extra.append(f"限流 {p['rate_limited_sec']}s")
                suffix = f" ({', '.join(extra)})" if extra else ""
                n_models = len(p["models"])
                print(f"  {icon} {p['name']:<12} {n_models} 个模型 | "
                      f"首选: {p['default_model']}{suffix}")
        elif args.cmd == "models":
            result = list_models(platform=args.platform, live=args.live)
            for pname, models in result.items():
                print(f"\n  {pname} ({len(models)} 个):")
                for i, mdl in enumerate(models):
                    tier = f"T{i}" if not args.live else "  "
                    print(f"    {tier} {mdl}")
    except LLMError as e:
        print(f"错误: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
