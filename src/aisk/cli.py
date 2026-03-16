import argparse
import sys

from aisk import __version__
from aisk.aliases import resolve_model
from aisk.client import stream_chat
from aisk.config import init_config, load_config
from aisk.output import render_quiet, render_verbose


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aisk",
        description="Ask any LLM from your terminal.",
        usage="%(prog)s [-q] <model> <message>\n       %(prog)s init\n       %(prog)s models\n       %(prog)s --version",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Output only the LLM response, no decoration.",
    )
    parser.add_argument("args", nargs="*", help=argparse.SUPPRESS)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(argv)
    positional = parsed.args

    if not positional:
        parser.print_help()
        return 2

    command = positional[0]

    if command == "init":
        for action in init_config():
            print(action)
        return 0

    if command == "models":
        cfg = load_config()
        for alias, model_name in sorted(cfg.aliases.items()):
            print(f"  {alias:12s} → {model_name}")
        return 0

    # Main flow: aisk <model> [message]
    model_input = command
    message: str | None = positional[1] if len(positional) > 1 else None

    if message is None:
        if sys.stdin.isatty():
            print("Error: no message provided. Pass it as an argument or pipe via stdin.", file=sys.stderr)
            return 2
        message = sys.stdin.read().strip()
        if not message:
            print("Error: empty stdin.", file=sys.stderr)
            return 2

    cfg = load_config()

    if not cfg.api_key:
        print("Error: AISK_API_KEY not set. Run 'aisk init' and edit ~/.aisk/.env", file=sys.stderr)
        return 1

    model = resolve_model(model_input, cfg.aliases)
    events = stream_chat(cfg.endpoint, cfg.api_key, model, message)

    if parsed.quiet:
        return render_quiet(events)
    else:
        return render_verbose(model, message, events)


if __name__ == "__main__":
    sys.exit(main())
