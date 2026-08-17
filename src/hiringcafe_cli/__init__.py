"""HiringCafe CLI package interface."""

import argparse
import sys

from hiringcafe_cli import probe
from hiringcafe_cli import search
from hiringcafe_cli import count
from hiringcafe_cli import job
from hiringcafe_cli.search_state import InvalidSearchState

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
    subparsers = parser.add_subparsers(dest="command")
    probe_parser = subparsers.add_parser("probe", help="run the opt-in live endpoint probe")
    probe_parser.set_defaults(handler=probe.main)
    search_parser = subparsers.add_parser("search", help="search jobs")
    search_parser.add_argument("query", nargs="?", default="")
    search_parser.add_argument("--page", type=int, default=0)
    search_parser.add_argument("--raw-search-state")
    search_parser.add_argument("--json", action="store_true")
    search_parser.set_defaults(handler=search.run)
    count_parser = subparsers.add_parser("count", help="print total result count")
    count_parser.add_argument("query", nargs="?", default="")
    count_parser.add_argument("--raw-search-state")
    count_parser.add_argument("--json", action="store_true")
    count_parser.set_defaults(handler=count.run)
    job_parser = subparsers.add_parser("job", help="inspect job details")
    job_subparsers = job_parser.add_subparsers(dest="job_command", required=True)
    job_show_parser = job_subparsers.add_parser("show", help="show a job description")
    job_show_parser.add_argument("object_id")
    job_show_parser.add_argument("--json", action="store_true")
    job_show_parser.set_defaults(handler=job.run)
    return parser


def main(argv: list[str] | None = None) -> None:
    """Run the command-line interface.

    Args:
        argv: Optional argv list; defaults to ``sys.argv[1:]``.
    """
    arguments = build_parser().parse_args(argv)
    handler = getattr(arguments, "handler", None)
    if handler is not None:
        json_output = getattr(arguments, "json", False)
        try:
            raise SystemExit(handler(arguments, json_output))
        except InvalidSearchState as error:
            print(f"hiringcafe: {error}", file=sys.stderr)
            raise SystemExit(2) from error
        except ValueError as error:
            print(f"hiringcafe: {error}", file=sys.stderr)
            raise SystemExit(1) from error
