import logging
import os
import sys
import webbrowser
from typing import Optional

import click

import linear

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
LOGGER = logging.getLogger(__name__)


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
        printer = linear.print.ConsolePrinter()

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
@click.option("--status", type=click.Choice(linear.ISSUE_STATES), default=None)
@click.option("--json", is_flag=True)
def cmd_issue_list(status: str, json: bool):
    """
    List linear issues assigned to you
    """

    issue_states = [status] if status else ["backlog", "started", "unstarted"]
    me = linear.get_me()

    if me.assigned_issues is None:
        print("No issues assigned to you")
        return

    issues = sorted(
        [
            # I need to fetch the issue to be able to load sub issues
            linear.get_issue(issue.id)
            for issue in me.assigned_issues
            if issue.state.type in issue_states
        ],
        key=lambda issue: issue.state.name,
    )

    printer = None
    if json:
        printer = linear.print.JsonPrinter(sys.stdout)
    else:
        printer = linear.print.ConsolePrinter()
    printer.print_issue_list(issues)


@cmd_issue.command("view")
@click.argument("issue_id", type=str)
@click.option("--web", is_flag=True)
@click.option("--json", is_flag=True)
def cmd_issue_view(issue_id: str, web: bool, json: bool):
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
        printer = linear.print.ConsolePrinter()

    printer.print_issue(issue)


@click.group()
def cli():
    setup_logging()


cli.add_command(cmd_issue)
cli.add_command(cmd_team)
if __name__ == "__main__":
    cli()
