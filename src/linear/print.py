import dataclasses
import json
import textwrap
import typing as t
from datetime import datetime

import colorama
from colorama import Fore, Style
from tabulate import tabulate

from . import highlight
from .models import Issue


class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class Printer(t.Protocol):
    def print_issue_list(self, issues: list[Issue]): ...

    def print_issue(self, issue: Issue): ...


class JsonPrinter(Printer):
    def __init__(self, out: t.TextIO):
        self.out = out

    def print_issue_list(self, issues: list[Issue]):
        json.dump(issues, self.out, cls=CustomEncoder)
        self.out.write("\n")

    def print_issue(self, issue: Issue):
        json.dump(issue, self.out, cls=CustomEncoder)
        self.out.write("\n")


class TablePrinter(Printer):
    def print_issue_list(self, issues: list[Issue]):
        data = [
            [
                issue.identifier,
                issue.title,
                issue.state.name,
                issue.assignee.name if issue.assignee else "Unassigned",
            ]
            for issue in issues
        ]
        headers = ["ID", "Title", "State", "Assignee"]
        return print(tabulate(data, headers=headers))

    def print_issue(self, issue: Issue):
        data = {
            "ID": issue.identifier,
            "Title": issue.title,
            "State": issue.state.name,
            "Assignee": issue.assignee.name if issue.assignee else "Unassigned",
            "Description": issue.description,
        }
        return print(tabulate(data.items()))


class ConsolePrinter(Printer):
    def __init__(self):
        colorama.init()

    def print_issue_list(self, issues: list[Issue]):
        text = ""

        for issue in issues:
            text += title_text(issue)

            # Sort the sub_issues by state
            sub_issues = sorted(issue.children, key=lambda x: x.state.name)

            for subissue in sub_issues:
                text += f"  {title_text(subissue)}"

        print(text, end="")

    def print_issue(self, issue: Issue):
        text = issue_text(issue)
        print(text, end="")


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
    title = f"{issue.identifier} - {issue.title} ({status})"
    if issue.assignee:
        title += f" ({Fore.MAGENTA}{issue.assignee.name}{Style.RESET_ALL})"

    return f"{title}\n"


def issue_text(issue: Issue):
    text = title_text(issue)

    if issue.description:
        description = issue.description.replace("\n\\", "\n")
        formatted_description = highlight.markdown(description)
        text += f"\n{formatted_description}"

    if show_subissues := issue.children:
        text += "Sub-issues:\n"
        # print("Sub-issues:")
        for subissue in show_subissues:
            subissue_text = subissue_as_formatted_text(subissue)
            text += subissue_text

    if issue.comments:
        comment_text = "\n"
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
        text += f"\n{comment_text}\n"

    url = f"{Fore.GREEN}" f"{issue.url}" f"{Style.RESET_ALL}"
    text += f"{url}\n"

    return text


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
