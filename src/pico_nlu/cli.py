"""Command-line interface: ``pico-nlu train|parse|eval``.

Subcommands are implemented in PRD-10 (CLI & Metrics). For now the CLI exists only so the
console entry point resolves and ``pico-nlu --help`` does not crash.
"""

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``pico-nlu`` console script.

    Returns a process exit code. Subcommands are not yet implemented.
    """
    parser = argparse.ArgumentParser(
        prog="pico-nlu",
        description="Train and run a pico-nlu model.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("train", help="Train a model from a dataset (not yet implemented).")
    subparsers.add_parser(
        "parse", help="Parse an utterance with a trained model (not yet implemented)."
    )
    subparsers.add_parser(
        "eval", help="Evaluate a trained model on a dataset (not yet implemented)."
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    print(f"error: '{args.command}' is not implemented yet", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
