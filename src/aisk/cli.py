import argparse
import sys

from aisk import __version__


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
        print("aisk init — not yet implemented")
        return 0

    if command == "models":
        print("aisk models — not yet implemented")
        return 0

    # Main flow: aisk <model> [message]
    model = command
    message: str | None = positional[1] if len(positional) > 1 else None

    if message is None:
        if sys.stdin.isatty():
            print("Error: no message provided. Pass it as an argument or pipe via stdin.", file=sys.stderr)
            return 2
        message = sys.stdin.read().strip()
        if not message:
            print("Error: empty stdin.", file=sys.stderr)
            return 2

    print(f"[aisk] model={model} quiet={parsed.quiet}")
    print(f"[aisk] message={message!r}")
    print("[aisk] not yet wired — see M4-M6")
    return 0


if __name__ == "__main__":
    sys.exit(main())
