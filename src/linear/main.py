import argparse
import os
import webbrowser

from colorama import Back, Fore, Style, init

from . import linear_client

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]


def view_issue(issue_id: str, web: bool = False):
    issue = linear_client.get_issue(issue_id)
    if web:
        webbrowser.open(issue.url)
        return

    print(f"{issue.title}\n")
    print(f"{issue.description}")
    print(f"{issue.url}")


def list_issues():
    init()
    client = linear_client.LinearClient(LINEAR_API_KEY)
    me = client.get_me()
    in_progress_issues = [
        issue for issue in me.assigned_issues if issue.state.name == "In Progress"
    ]
    for issue in in_progress_issues:
        # title_color = Fore.GREEN if issue.state.name == "Done" else Fore.RED
        match issue.state.name:
            case "Done":
                status_color = Fore.GREEN
            case "In Progress":
                status_color = Fore.YELLOW
            case _:
                status_color = Fore.RED

        status = f"{status_color}{issue.state.name}{Style.RESET_ALL}"

        print(f"{issue.title} ({status})")
        print(f"{issue.description}")
        print()
        print(f"{issue.url}")


def view_user():
    # List issues assigned to me
    pass


def cli():
    # linear issue list
    # linear issue view <issue_id>

    # Examples:
    # linear issue view TRA-331
    # linear issue view TRA-331 --web

    # linear team list
    # linear team view <team_id>

    parser = argparse.ArgumentParser(description="Linear CLI")

    subparsers = parser.add_subparsers(dest="command")

    issue_parser = subparsers.add_parser("issue")
    issue_subparsers = issue_parser.add_subparsers(dest="issue_command")

    issue_list_parser = issue_subparsers.add_parser("list")
    issue_list_parser.add_argument("--project", type=str, help="Project ID")

    issue_view_parser = issue_subparsers.add_parser("view")
    issue_view_parser.add_argument("issue_id", type=str, help="Issue ID")

    issue_view_parser.add_argument(
        "--web", action="store_true", help="Open issue in browser"
    )

    team_parser = subparsers.add_parser("team")
    team_subparsers = team_parser.add_subparsers(dest="team_command")

    team_list_parser = team_subparsers.add_parser("list")

    team_view_parser = team_subparsers.add_parser("view")

    args = parser.parse_args()

    if args.command == "issue":
        if args.issue_command == "list":
            list_issues()
        elif args.issue_command == "view":
            view_issue(args.issue_id, web=args.web)


def main():
    client = linear_client.LinearClient(LINEAR_API_KEY)
    issue = client.get_issue("TRA-383")
    me = client.get_me()
    print(f"Hello {me.name}! Your email is {me.email}")

    issue = client.get_issue("TRA-383")
    print(f"Found issue {issue.title} with description {issue.description}")

    teams = client.get_teams()
    print(f"Found {len(teams)} teams")


if __name__ == "__main__":
    main()
