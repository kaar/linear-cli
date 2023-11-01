import logging
import os
import webbrowser
from collections import defaultdict

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


@click.group("issue")
def cmd_issue():
    """
    linear issue <subcommand>
    """


@cmd_issue.command("list")
@click.option("--done", is_flag=True, help="Completed")
@click.option("--cancelled", is_flag=True, help="Cancelled")
@click.option("--all", is_flag=True, help="All issues")
@click.option("--show-description", is_flag=True, help="Show issue description")
def cmd_issue_list(done: bool, cancelled: bool, all: bool, show_description: bool):
    """
    linear issue list
    """
    all_states = ["In Progress", "Done", "Prioritized backlog"]
    accepted_states = ["In Progress", "Prioritized backlog", "Under review"]

    if all:
        accepted_states = all_states
    elif done:
        accepted_states.append("Done")
    elif cancelled:
        accepted_states.append("Cancelled")

    me = linear.get_me()

    # Group issues by `issue.state.name`
    issues_by_state = defaultdict(list)
    for item in me.assigned_issues:
        issues_by_state[item.state.name].append(item)

    issues_to_print = [
        issue
        for state, issues in issues_by_state.items()
        if state in accepted_states
        for issue in issues
    ]

    for issue in issues_to_print:
        linear.print.print_issue(
            issue,
            show_description=show_description,
            show_url=False,
        )


@cmd_issue.command("view")
@click.argument("issue_id", type=str)
@click.option("--web", is_flag=True)
@click.option("--comments", is_flag=True)
def cmd_issue_view(issue_id: str, web: bool, comments: bool):
    """
    linear issue view <issue_id>
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

    linear.print.print_issue(
        issue,
        show_description=True,
        show_comments=comments,
        show_url=True,
    )


@click.group()
def cli():
    setup_logging()


cli.add_command(cmd_issue)
if __name__ == "__main__":
    cli()
