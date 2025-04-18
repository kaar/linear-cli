import json
import dataclasses
from datetime import datetime
from typing import Literal
import textwrap

import colorama
from colorama import Fore, Style

from . import highlight
from .client import Issue, User

colorama.init()

Format = Literal["markdown", "text", "json"]


class DataclassJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class LinearPrinter:
    def __init__(self, format: Format = "markdown"):
        self._format = format

    def print_me(
        self,
        me: User,
        issues: list[Issue],
    ):
        match self._format:
            case "json":
                print(json.dumps(issues, cls=DataclassJsonEncoder))
                return
            case "markdown":
                print(me_markdown(me, issues))
                return

    def print_issues(
        self,
        issues: list[Issue],
    ):
        match self._format:
            case "json":
                print(json.dumps(issues, cls=DataclassJsonEncoder))
                return
            case "markdown":
                print(issues_markdown(issues), end="")
                return

    def print_issue(
        self,
        issue: Issue,
    ):
        match self._format:
            case "json":
                print(json.dumps(issue, cls=DataclassJsonEncoder))
                return
            case "markdown":
                print(issue_markdown(issue), end="")
                return


def issue_markdown(issue: Issue):
    text = title_text(issue)
    url = f"{Fore.GREEN}{issue.url}{Style.RESET_ALL}"
    text += f"<{url}>\n"

    if issue.description:
        text += description_text(issue.description)

    if show_subissues := issue.children:
        text += "Sub-issues:\n"
        # print("Sub-issues:")
        for subissue in show_subissues:
            subissue_text = subissue_as_formatted_text(subissue)
            text += subissue_text

    if issue.comments:
        comment_text = "## Comments\n"
        comments = sorted(issue.comments, key=lambda x: x.created_at)
        for comment in comments:
            # Skip replies
            if comment.parent_id:
                continue
            comment_text += (
                f"{Fore.BLUE}"
                f"@{comment.user_name}{date_format(comment.created_at)}"
                f"{Style.RESET_ALL}\n"
            )
            comment_text += f"{highlight.markdown(comment.body)}\n"
            replies = [
                reply for reply in issue.comments if reply.parent_id == comment.id
            ]
            for reply in replies:
                comment_text += (
                    f"{Fore.LIGHTBLUE_EX}"
                    f"@{reply.user_name}{date_format(reply.created_at)}"
                    f"{Style.RESET_ALL}\n"
                )
                # TODO: Indent the whole reply by 4 spaces
                comment_text += f"    {reply.body}\n\n"
        text += f"\n{highlight.markdown(comment_text)}\n"

    # TODO: I don't like how it looks but it works
    if issue.attachments:
        github_attachments = [
            attachment
            for attachment in issue.attachments
            if attachment.source_type == "github"
        ]
        if github_attachments:
            github_text_section = "## Pull Requests\n"
            for attachment in github_attachments:
                github_text_section += f"* [{attachment.title}]({attachment.url})\n"
            text += highlight.markdown(github_text_section)

        slack_attachments = [
            attachment
            for attachment in issue.attachments
            if attachment.source_type == "slack"
        ]
        if slack_attachments:
            slack_text_section = "## Slack\n"
            for attachment in slack_attachments:
                slack_text_section += f"* [{attachment.title}]({attachment.url})\n"
            text += highlight.markdown(slack_text_section)

    return text


def me_markdown(_, issues: list[Issue]):
    text = ""

    for issue in issues:
        text += title_text(issue)
        text += description_text(issue.description)

        # Sort the sub_issues by state
        sub_issues = sorted(issue.children, key=lambda x: x.state.name)

        for subissue in sub_issues:
            text += f"  {title_text(subissue)}"
            text += description_text(subissue.description)

    print(text, end="")


def issues_markdown(issues: list[Issue]):
    text = ""

    for issue in issues:
        text += title_text(issue)

        # Sort the sub_issues by state
        sub_issues = sorted(issue.children, key=lambda x: x.state.name)

        for subissue in sub_issues:
            text += f"  {title_text(subissue)}"

    return text


def title_text(issue: Issue):
    status_color = {
        "triage": Fore.CYAN,
        "backlog": Fore.CYAN,
        "completed": Fore.GREEN,
        "started": Fore.YELLOW,
        "unstarted": Fore.BLUE,
        "canceled": Fore.RED,
    }[issue.state.type]

    status = f"{status_color}{issue.state.name}{Style.RESET_ALL}"
    title = f"{Fore.LIGHTCYAN_EX}{issue.identifier}{Style.RESET_ALL} - {issue.title} ({status})"
    if issue.assignee:
        title += f" ({Fore.MAGENTA}{issue.assignee.name}{Style.RESET_ALL})"

    return f"{title}\n"


def description_text(description: str):
    if not description:
        return ""
    description = description.replace("\n\\", "\n")
    formatted_description = highlight.markdown(description)
    return f"\n{formatted_description}"


def wrap_preserve_newlines(text, width=120, break_long_words=False):
    lines = text.split("\n")
    wrapped_lines = [
        textwrap.fill(line, width=width, break_long_words=break_long_words)
        for line in lines
    ]
    wrapped_text = "\n".join(wrapped_lines)
    indent_width = 2
    return textwrap.indent(wrapped_text, " " * indent_width)


def date_format(date: datetime):
    return f" ({date.strftime('%Y-%m-%d - %H:%M:%S')})"


def subissue_as_formatted_text(issue: Issue):
    formated_text = ""

    match issue.state.name:
        case "Done":
            status_color = Fore.GREEN
        case "In Progress":
            status_color = Fore.YELLOW
        case "Prioritized backlog":
            status_color = Fore.BLUE
        case _:
            status_color = Fore.RED

    status = f"{status_color}{issue.state.name}{Style.RESET_ALL}"
    title = f"{issue.title} {issue.identifier}"
    meta_data = f"({status})"
    formated_text += f"{title}\n"
    formated_text += f"{meta_data}\n"

    return formated_text
