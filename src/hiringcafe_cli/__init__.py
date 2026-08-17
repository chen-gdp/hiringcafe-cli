"""HiringCafe CLI package interface."""

import argparse
import sys

from hiringcafe_cli import probe
from hiringcafe_cli import search
from hiringcafe_cli import count
from hiringcafe_cli import job
from hiringcafe_cli import auth
from hiringcafe_cli import saved_jobs_list
from hiringcafe_cli import saved_jobs_save
from hiringcafe_cli import saved_jobs_stage
from hiringcafe_cli import saved_jobs_remove
from hiringcafe_cli.firebase import FirebaseAuthError, FirebaseTransportError
from hiringcafe_cli.saved_jobs import VALID_STAGES
from hiringcafe_cli.saved_jobs_list import FirestoreError
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
    auth_parser = subparsers.add_parser("auth", help="manage Firebase authentication")
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command", required=True)
    auth_login_parser = auth_subparsers.add_parser("login", help="log in to Firebase")
    auth_login_parser.add_argument("--email", required=True)
    auth_login_parser.set_defaults(handler=auth.login_email)
    auth_import_parser = auth_subparsers.add_parser("import", help="import a refresh token")
    auth_import_parser.set_defaults(handler=auth.import_token)
    auth_status_parser = auth_subparsers.add_parser("status", help="show credential status")
    auth_status_parser.add_argument("--json", action="store_true")
    auth_status_parser.set_defaults(handler=auth.status)
    auth_logout_parser = auth_subparsers.add_parser("logout", help="remove the local session")
    auth_logout_parser.set_defaults(handler=auth.logout)
    saved_parser = subparsers.add_parser("saved-jobs", help="manage saved jobs")
    saved_subparsers = saved_parser.add_subparsers(dest="saved_command", required=True)
    saved_list_parser = saved_subparsers.add_parser("list", help="list saved jobs")
    saved_list_parser.add_argument("--stage", choices=sorted(VALID_STAGES))
    saved_list_parser.add_argument("--json", action="store_true")
    saved_list_parser.set_defaults(handler=saved_jobs_list.run)
    saved_save_parser = saved_subparsers.add_parser("save", help="save a job")
    saved_save_parser.add_argument("object_id")
    saved_save_parser.add_argument("--stage", default="saved")
    saved_save_parser.set_defaults(handler=saved_jobs_save.run)
    saved_stage_parser = saved_subparsers.add_parser("stage", help="update a job stage")
    saved_stage_parser.add_argument("object_id")
    saved_stage_parser.add_argument("--stage", required=True)
    saved_stage_parser.set_defaults(handler=saved_jobs_stage.run)
    saved_remove_parser = saved_subparsers.add_parser("remove", help="remove a saved job")
    saved_remove_parser.add_argument("object_id")
    saved_remove_parser.add_argument("--yes", action="store_true")
    saved_remove_parser.set_defaults(handler=saved_jobs_remove.run)
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
        except FirebaseAuthError as error:
            print(f"hiringcafe: {error}", file=sys.stderr)
            raise SystemExit(5) from error
        except FirebaseTransportError as error:
            print(f"hiringcafe: {error}", file=sys.stderr)
            raise SystemExit(1) from error
        except FirestoreError as error:
            print(f"hiringcafe: {error}", file=sys.stderr)
            raise SystemExit(1) from error
