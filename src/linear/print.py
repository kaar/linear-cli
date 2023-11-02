import dataclasses
import json
import textwrap
import typing as t
from datetime import datetime

import colorama
from colorama import Fore, Style
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers.markup import MarkdownLexer

from .models import Issue


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


class Printer(t.Protocol):
    def print_issue_list(self, issues: list[Issue]):
        ...

    def print_issue(self, issue: Issue):
        ...


class JsonPrinter(Printer):
    def __init__(self, out: t.TextIO):
        self.out = out

    def print_issue_list(self, issues: list[Issue]):
        json.dump(issues, self.out, cls=CustomEncoder, indent=2)

    def print_issue(self, issue: Issue):
        json.dump(issue, self.out, cls=CustomEncoder, indent=2)


class ConsolePrinter(Printer):
    def __init__(self, include_comments: bool):
        colorama.init()
        self.include_comments = include_comments

    def print_issue_list(self, issues: list[Issue]):
        text = ""

        for issue in issues:
            text += title_text(issue)

        # if show_subissues := issue.children:
        #     text += "Sub-issues:\n"
        #     # print("Sub-issues:")
        #     for subissue in show_subissues:
        #         subissue_text = subissue_as_formatted_text(subissue)
        #         text += subissue_text
        print(text, end="")

    def print_issue(self, issue: Issue):
        text = issue_text(issue, self.include_comments)
        print(text, end="")


def title_text(issue: Issue):
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
    title = f"{issue.identifier} - {issue.title} ({status})"

    return f"{title}\n"


def issue_text(issue: Issue, show_comments):
    text = title_text(issue)

    if issue.description:
        description = issue.description.replace("\n\\", "\n")
        formatted_description = markdown_format(description)
        text += f"\n{formatted_description}"

    if show_subissues := issue.children:
        text += "Sub-issues:\n"
        # print("Sub-issues:")
        for subissue in show_subissues:
            subissue_text = subissue_as_formatted_text(subissue)
            text += subissue_text

    if issue.comments:
        comment_text = ""
        if show_comments:
            comment_text = "\n"
            for comment in issue.comments:
                comment_text += (
                    f"{Fore.BLUE}"
                    f"{comment.user_name}{date_format(comment.created_at)}"
                    f"{Style.RESET_ALL}\n"
                )
                comment_text += markdown_format(comment.body)
        else:
            comment_text = (
                f"{Fore.RED}"
                f"--- Not showing {len(issue.comments)} comments ---"
                f"{Style.RESET_ALL}"
            )

        text += f"{comment_text}\n"

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


def markdown_format(description: str):
    formatted_text = wrap_preserve_newlines(description)
    highlighted_test = highlight(formatted_text, MarkdownLexer(), TerminalFormatter())
    return highlighted_test


def date_format(date: str):
    datetime_parsed = datetime.fromisoformat(date)
    return f" ({datetime_parsed.strftime('%Y-%m-%d - %H:%M:%S')})"


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
