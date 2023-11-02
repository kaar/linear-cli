import logging
import os
import sys
import webbrowser
from collections import defaultdict
from typing import Optional

import click

import linear

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
LOGGER = logging.getLogger(__name__)

OPEN_STATES = ["In Progress", "Under review"]
CLOSED_STATES = ["Done"]
ALL_STATES = OPEN_STATES + CLOSED_STATES


def setup_logging():
    DEBUG = os.environ.get("DEBUG", False)
    log_level = logging.DEBUG if DEBUG else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    LOGGER.debug("Debug mode enabled")


@click.command("team")
@click.option("--json", is_flag=True)
@click.option("--status", type=click.Choice(linear.ISSUE_STATES), default=None)
def cmd_team(status: Optional[str], json: bool):
    """
    linear team
    """
    me = linear.get_me()

    printer = None
    if json:
        printer = linear.print.JsonPrinter(sys.stdout)
    else:
        printer = linear.print.ConsolePrinter(include_comments=False)

    if not me.teams:
        LOGGER.error("You are not a member of any teams")
        sys.exit(1)

    issue_states = [status] if status else linear.ISSUE_STATES

    for team in me.teams:
        team_issues = linear.get_team(team.id).issues
        issues = sorted(
            [issue for issue in team_issues if issue.state.type in issue_states],
            key=lambda issue: issue.state.name,
        )

        printer.print_issue_list(issues)


@click.group("issue")
def cmd_issue():
    """
    linear issue <subcommand>
    """


@cmd_issue.command("list")
@click.option(
    "-s",
    "--state",
    type=click.Choice(["open", "closed", "all"]),
    default="open",
    help='Filter by state: {open|closed|all} (default "open")',
)
@click.option("--json", is_flag=True)
def cmd_issue_list(state, json: bool):
    """
    List linear issues assigned to you
    """

    match state:
        case "open":
            selected_states = OPEN_STATES
        case "closed":
            selected_states = CLOSED_STATES
        case _:
            selected_states = ALL_STATES

    me = linear.get_me()

    # Group issues by `issue.state.name`
    issues_by_state = defaultdict(list)
    for item in me.assigned_issues:
        issues_by_state[item.state.name].append(item)

    issues_to_print = [
        issue
        for state, issues in issues_by_state.items()
        if state in selected_states
        for issue in issues
    ]

    printer = None
    if json:
        printer = linear.print.JsonPrinter(sys.stdout)
    else:
        printer = linear.print.ConsolePrinter(include_comments=False)
    printer.print_issue_list(issues_to_print)


@cmd_issue.command("view")
@click.argument("issue_id", type=str)
@click.option("--web", is_flag=True)
@click.option("--comments", is_flag=True)
@click.option("--json", is_flag=True)
def cmd_issue_view(issue_id: str, web: bool, comments: bool, json: bool):
    """
    linear issue view <issue_id>

    TODO: Examples
    """

    def get_issue_id(issue: str) -> str:
        if issue.startswith("http"):
            # TODO: Validate url,
            # https://linear.app/linear-oss/issue/TRA-383/linear-cli
            # Validate issue id after parsing
            return issue_id.split("/")[-2]
        else:
            return issue_id

    issue_id = get_issue_id(issue_id)

    issue = linear.get_issue(issue_id)
    if web:
        webbrowser.open(issue.url)
        return

    printer = None
    if json:
        printer = linear.print.JsonPrinter(sys.stdout)
    else:
        printer = linear.print.ConsolePrinter(include_comments=comments)

    printer.print_issue(issue)


@click.group()
def cli():
    setup_logging()


cli.add_command(cmd_issue)
cli.add_command(cmd_team)
if __name__ == "__main__":
    cli()
