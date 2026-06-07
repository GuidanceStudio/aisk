import argparse
import sys

from aisk import __version__, session
from aisk.aliases import resolve_model
from aisk.chat import chat
from aisk.client import ContentChunk, stream_chat
from aisk.completions import generate_bash, generate_refresh, generate_shortcuts, generate_zsh, install_completions
from aisk.config import ConfigError, ensure_config, init_config, interactive_init, load_config, sync_aliases
from aisk.output import render_quiet, render_quiet_buffered, render_verbose, render_verbose_buffered


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aisk",
        description="Ask any LLM from your terminal.",
        usage=(
            "%(prog)s [-q] [-S] <model> [message]\n"
            "       %(prog)s init\n"
            "       %(prog)s sync\n"
            "       %(prog)s models\n"
            "       %(prog)s shortcuts\n"
            "       %(prog)s completions <bash|zsh|install|refresh>\n"
            "       %(prog)s --resume [message]\n"
            "       %(prog)s --version"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "commands:\n"
            "  init          create ~/.aisk config and set/update AISK_API_KEY\n"
            "  sync          refresh default aliases while keeping custom config\n"
            "  models        list configured model aliases\n"
            "  shortcuts     print shell shortcut functions from conf.toml\n"
            "  completions   generate, install, or refresh shell completions\n"
            "\n"
            "examples:\n"
            "  aisk cls46                 start interactive chat\n"
            "  aisk ge31lite \"hello\"      ask one question\n"
            "  aisk --resume              reopen the last conversation\n"
        ),
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
    parser.add_argument(
        "--resume", action="store_true",
        help="Continue the last conversation (chat, or one-shot with a message).",
    )
    parser.add_argument("args", nargs="*", help=argparse.SUPPRESS)

    return parser


def _run_oneshot(cfg, model: str, messages: list[dict], *, quiet: bool, no_stream: bool) -> int:
    """Stream a one-shot reply, render it, and persist the conversation on success."""
    collected: list[str] = []

    def _tee(events):
        for event in events:
            if isinstance(event, ContentChunk):
                collected.append(event.text)
            yield event

    events = _tee(
        stream_chat(cfg.endpoint, cfg.api_key, model, messages, prompt_cache=cfg.prompt_cache)
    )
    header = messages[-1]["content"]
    if quiet and no_stream:
        code = render_quiet_buffered(events)
    elif quiet:
        code = render_quiet(events)
    elif no_stream:
        code = render_verbose_buffered(model, header, events)
    else:
        code = render_verbose(model, header, events)

    if code == 0 and collected:
        session.save_session(
            model, messages + [{"role": "assistant", "content": "".join(collected)}]
        )
    return code


def _resume(parsed, positional: list[str]) -> int:
    """Handle `aisk --resume [message]`."""
    data = session.load_session()
    if not data:
        print("Error: nothing to resume.", file=sys.stderr)
        return 1
    model = data["model"]
    history = list(data["messages"])

    message: str | None = " ".join(positional) if positional else None
    if not message and not sys.stdin.isatty():
        message = sys.stdin.read().strip() or None

    try:
        cfg = ensure_config()
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if message is None:
        print(f"Resuming {model} — {len(history)} messages", file=sys.stderr)
        return chat(model, cfg, history=history)

    messages = history + [{"role": "user", "content": message}]
    return _run_oneshot(cfg, model, messages, quiet=parsed.quiet, no_stream=parsed.no_stream)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(argv)
    positional = parsed.args

    if parsed.resume:
        return _resume(parsed, positional)

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

    if command == "sync":
        summary = sync_aliases()

        def _fmt(items: list[str]) -> str:
            return ", ".join(items) if items else "(none)"

        print("Synced ~/.aisk/conf.toml aliases to current defaults.")
        print(f"  + added:   {_fmt(summary['added'])}")
        print(f"  ~ updated: {_fmt(summary['updated'])}")
        print(f"  - removed: {_fmt(summary['removed'])}")
        print(f"  = kept custom: {_fmt(summary['kept'])}")
        print('\nRefresh tab-completion:  eval "$(aisk completions refresh)"')
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

    # No message: interactive chat on a TTY, otherwise read from stdin.
    interactive_chat = False
    if not message:
        if sys.stdin.isatty():
            interactive_chat = True
        else:
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

    if interactive_chat:
        return chat(model, cfg, model_input=model_input)

    return _run_oneshot(
        cfg, model, [{"role": "user", "content": message}],
        quiet=parsed.quiet, no_stream=parsed.no_stream,
    )


if __name__ == "__main__":
    sys.exit(main())
