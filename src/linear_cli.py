import argparse
import os
import webbrowser
from collections import defaultdict

from colorama import Back, Fore, Style, init

import linear

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]


def print_issue(issue: linear.Issue):
    print(f"{issue.title}\n")
    print(f"{issue.description}")
    print(f"{issue.url}")


def list_issues(accepted_states: list[str]):
    init()
    me = linear.get_me()

    # Group issues by `issue.state.name`
    issues_by_state = defaultdict(list)
    for item in me.assigned_issues:
        issues_by_state[item.state.name].append(item)

    selected_states = [
        state for state in issues_by_state.keys() if state in accepted_states
    ]

    if len(selected_states) == 0:
        print(f"No issues in ({', '.join(accepted_states)})")
        # Print the count of issues in each stated
        for state, issues in issues_by_state.items():
            print(f"{state} ({len(issues)})")
        return

    for state, issues in issues_by_state.items():
        if state not in selected_states:
            continue

        match state:
            case "Done":
                status_color = Fore.GREEN
            case "In Progress":
                status_color = Fore.YELLOW
            case "Prioritized backlog":
                status_color = Fore.BLUE
            case _:
                status_color = Fore.RED

        status = f"{status_color}{state}{Style.RESET_ALL}"
        for issue in issues:
            print()
            identifier = f"{Fore.GREEN}{issue.identifier}{Style.RESET_ALL}"
            print(f"{identifier} - {issue.title} ({status})")
            print(f"{issue.url}")


def view_user():
    # List issues assigned to me
    pass


def issue_list(args):
    """
    linear issue list
    linear issue list --all
    linear issue list --cancelled
    linear issue list --completed
    """
    all_states = ["In Progress", "Done", "Prioritized backlog"]
    accepted_states = ["In Progress", "Prioritized backlog"]

    if args.all:
        accepted_states = all_states
    elif args.done:
        accepted_states.append("Done")
    elif args.cancelled:
        accepted_states.append("Cancelled")

    list_issues(accepted_states)


def issue_view(args):
    """
    linear issue view <issue_id>

    Options:
        --web - open issue in browser

    Examples:
    linear-cli issue view TRA-683
    """

    def get_issue_id(issue: str) -> str:
        if issue.startswith("http"):
            return args.issue.split("/")[-2]
        else:
            return args.issue

    issue_id = get_issue_id(args.issue)

    issue = linear.get_issue(issue_id)
    if args.web:
        webbrowser.open(issue.url)
        return

    print_issue(issue)


def cli():
    parser = argparse.ArgumentParser(description="Linear CLI")
    subparsers = parser.add_subparsers(dest="command")
    issue_parser = subparsers.add_parser("issue")

    # Issue subcommands
    issue_subparsers = issue_parser.add_subparsers(dest="issue_command")

    # Issue list
    issue_list_parser = issue_subparsers.add_parser("list")
    issue_list_parser.add_argument("--done", action="store_true", help="Completed")
    issue_list_parser.add_argument("--all", action="store_true", help="All")
    issue_list_parser.add_argument("--cancelled", action="store_true", help="Cancelled")
    issue_list_parser.set_defaults(func=issue_list)

    # Issue view
    issue_view_parser = issue_subparsers.add_parser("view")
    issue_view_parser.add_argument("issue", type=str, help="Issue Id or Url")
    issue_view_parser.add_argument(
        "--web", action="store_true", help="Open issue in browser"
    )
    issue_view_parser.set_defaults(func=issue_view)

    args = parser.parse_args()
    match args:
        case None:
            parser.print_help()
        case _:
            args.func(args)


def main():
    issue = linear.get_issue("TRA-383")
    me = linear.get_me()
    print(f"Hello {me.name}! Your email is {me.email}")

    issue = linear.get_issue("TRA-383")
    print(f"Found issue {issue.title} with description {issue.description}")


if __name__ == "__main__":
    main()