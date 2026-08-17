"""HiringCafe CLI package interface."""

import argparse

__version__ = "0.1.0"

EXIT_CONTRACT = """\
Exit codes:
  0 success
  1 transport, HTTP, parsing, or API error
  2 invalid arguments or search state
  3 rate limited
  4 no stored credential
  5 stored credential rejected
  6 write conflict or prerequisite missing
"""


def build_parser() -> argparse.ArgumentParser:
    """Build the root CLI parser.

    Returns:
        An argparse parser implementing the PR 0.1 bootstrap contract.
    """
    parser = argparse.ArgumentParser(
        prog="hiringcafe",
        description="Hiring Cafe command-line interface",
        epilog=EXIT_CONTRACT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> None:
    """Run the command-line interface.

    Args:
        argv: Optional argv list; defaults to ``sys.argv[1:]``.
    """
    build_parser().parse_args(argv)
