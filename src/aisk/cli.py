import argparse
import sys

from aisk import __version__
from aisk.aliases import resolve_model
from aisk.client import stream_chat
from aisk.completions import generate_bash, generate_refresh, generate_shortcuts, generate_zsh, install_completions
from aisk.config import ConfigError, ensure_config, init_config, interactive_init, load_config
from aisk.output import render_quiet, render_quiet_buffered, render_verbose, render_verbose_buffered


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aisk",
        description="Ask any LLM from your terminal.",
        usage="%(prog)s [-q] <model> <message>\n       %(prog)s init\n       %(prog)s models\n       %(prog)s shortcuts\n       %(prog)s --version",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Output only the LLM response, no decoration.",
    )
    parser.add_argument(
        "-S", "--no-stream", action="store_true",
        help="Buffer the full response and print at the end instead of streaming.",
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
        if sys.stdin.isatty():
            interactive_init()
        else:
            for action in init_config():
                print(action)
        return 0

    if command == "completions":
        sub = positional[1] if len(positional) > 1 else None
        if sub == "bash":
            print(generate_bash())
        elif sub == "zsh":
            print(generate_zsh())
        elif sub == "install":
            print(install_completions())
        elif sub == "refresh":
            print(generate_refresh())
        else:
            print("Usage: aisk completions <bash|zsh|install|refresh>", file=sys.stderr)
            return 2
        return 0

    if command == "models":
        cfg = load_config()
        # Group aliases by provider (text before '/')
        groups: dict[str, list[tuple[str, str]]] = {}
        for alias, model_name in sorted(cfg.aliases.items()):
            provider = model_name.split("/", 1)[0] if "/" in model_name else "Other"
            groups.setdefault(provider, []).append((alias, model_name))

        # Provider display names: capitalize first letter
        first = True
        for provider in sorted(groups):
            if not first:
                print()
            first = False
            print(f"  {provider.capitalize()}")
            for alias, model_name in groups[provider]:
                print(f"    {alias:12s} {model_name}")
        return 0

    if command == "shortcuts":
        output = generate_shortcuts()
        if output:
            print(output, end="")
        else:
            print("No shortcuts configured. Add a [shortcuts] section to ~/.aisk/conf.toml")
        return 0

    # Main flow: aisk <model> [message words...]
    model_input = command
    message: str | None = " ".join(positional[1:]) if len(positional) > 1 else None

    if not message:
        if sys.stdin.isatty():
            print("Error: no message provided. Pass it as an argument or pipe via stdin.", file=sys.stderr)
            return 2
        message = sys.stdin.read().strip()
        if not message:
            print("Error: empty stdin.", file=sys.stderr)
            return 2

    try:
        cfg = ensure_config()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    model = resolve_model(model_input, cfg.aliases)
    events = stream_chat(cfg.endpoint, cfg.api_key, model, message)

    if parsed.quiet and parsed.no_stream:
        return render_quiet_buffered(events)
    elif parsed.quiet:
        return render_quiet(events)
    elif parsed.no_stream:
        return render_verbose_buffered(model, message, events)
    else:
        return render_verbose(model, message, events)


if __name__ == "__main__":
    sys.exit(main())
