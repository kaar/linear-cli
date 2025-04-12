import logging
import os
import sys
import webbrowser
from typing import Optional

import click

from . import console
from .cache import XDGCache
from .client import ISSUE_STATES, LinearClient

LOGGER = logging.getLogger(__name__)
LINEAR_CLIENT = LinearClient(
    url="https://api.linear.app/graphql",
    api_key=os.environ["LINEAR_API_KEY"],
    cache=XDGCache(app_name="linear"),
)


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
@click.option("--table", is_flag=True)
@click.option("--state", type=click.Choice(ISSUE_STATES), default=None)
def cmd_team(state: Optional[str], json: bool, table: bool):
    """
    linear team
    """
    me = LINEAR_CLIENT.get_me()
    if not me.teams:
        LOGGER.error("You are not a member of any teams")
        sys.exit(1)

    issue_states = [state] if state else ISSUE_STATES

    for team in me.teams:
        team_issues = LINEAR_CLIENT.get_team(team.id).issues
        issues = sorted(
            [issue for issue in team_issues if issue.state.type in issue_states],
            key=lambda issue: issue.state.name,
        )
        format = "json" if json else "table" if table else "markdown"
        console.print_issues(issues, format)


@click.group("issue")
def cmd_issue():
    """
    linear issue <subcommand>
    """


@cmd_issue.command("list")
@click.option("--state", type=click.Choice(ISSUE_STATES), default=None)
@click.option("--json", is_flag=True)
def cmd_issue_list(state: str, json: bool):
    """
    List linear issues assigned to you
    """
    issue_states = [state] if state else ["backlog", "started", "unstarted"]
    me = LINEAR_CLIENT.get_me()

    if me.assigned_issues is None:
        # print("No issues assigned to you")
        return

    issues = sorted(
        [
            # I need to fetch the issue to be able to load sub issues
            LINEAR_CLIENT.get_issue(issue.id)
            for issue in me.assigned_issues
            if issue.state.type in issue_states
        ],
        key=lambda issue: issue.state.name,
    )
    format = "json" if json else "markdown"
    console.print_issues(issues, format)


def complete_issue_id(ctx, param, incomplete):
    me = LINEAR_CLIENT.get_me()
    issue_states = ["backlog", "started", "unstarted"]
    return [
        issue.identifier
        for issue in me.assigned_issues
        if issue.state.type in issue_states and issue.identifier.startswith(incomplete)
    ]


@cmd_issue.command("view")
@click.argument("issue_id", type=str, shell_complete=complete_issue_id)
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

    issue = LINEAR_CLIENT.get_issue(issue_id)
    if web:
        webbrowser.open(issue.url)
        return

    format = "json" if json else "markdown"
    console.print_issue(issue, format)


@click.command("me")
@click.option("--json", is_flag=True)
@click.option("--state", type=click.Choice(ISSUE_STATES), default=None)
def cmd_me(state: str, json: bool):
    """
    List linear issues assigned to you
    """
    issue_states = [state] if state else ["backlog", "started", "unstarted"]
    me = LINEAR_CLIENT.get_me()

    if me.assigned_issues is None:
        # print("No issues assigned to you")
        return

    issues = sorted(
        [
            # I need to fetch the issue to be able to load sub issues
            LINEAR_CLIENT.get_issue(issue.id)
            for issue in me.assigned_issues
            if issue.state.type in issue_states
        ],
        key=lambda issue: issue.state.name,
    )
    format = "json" if json else "markdown"
    console.print_me(me, issues, format)


@click.command("ls")
@click.option("--state", type=click.Choice(ISSUE_STATES), default=None)
@click.option("--json", is_flag=True)
def cmd_ls(state: str, json: bool):
    """
    List linear issues assigned to you
    """
    issue_states = [state] if state else ["backlog", "started", "unstarted"]
    me = LINEAR_CLIENT.get_me()

    if me.assigned_issues is None:
        # print("No issues assigned to you")
        return

    issues = sorted(
        [
            # I need to fetch the issue to be able to load sub issues
            LINEAR_CLIENT.get_issue(issue.id)
            for issue in me.assigned_issues
            if issue.state.type in issue_states
        ],
        key=lambda issue: issue.state.name,
    )
    format = "json" if json else "markdown"
    console.print_issues(issues, format)


@click.group()
def cli():
    setup_logging()


cli.add_command(cmd_issue)
cli.add_command(cmd_team)
cli.add_command(cmd_me)
cli.add_command(cmd_ls)
if __name__ == "__main__":
    cli()
