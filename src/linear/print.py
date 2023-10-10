import textwrap

from colorama import Fore, Style, init
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers.markup import MarkdownLexer

from .models import Issue

init()


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


def issue_as_formatted_text(issue: Issue, show_description: bool = False):
    issue_text = ""

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

    issue_text += f"{title}\n"
    issue_text += f"{meta_data}\n"

    if show_description:
        if issue.description:
            description = issue.description.replace("\n\\", "\n")
            issue_text += markdown_format(description)

    if show_subissues := issue.children:
        issue_text += "Sub-issues:\n"
        # print("Sub-issues:")
        for subissue in show_subissues:
            issue_as_formatted_text(subissue, show_description=False)

    url = f"{Fore.GREEN}{issue.url}{Style.RESET_ALL}"
    issue_text += f"\n{url}"
    return issue_text


def print_issue(issue: Issue, show_description: bool = False):
    issue_text = issue_as_formatted_text(issue, show_description=show_description)
    print(issue_text)
