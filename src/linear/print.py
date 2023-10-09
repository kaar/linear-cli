from colorama import Fore, Style, init

from .models import Issue

init()


def print_description(description: str):
    if not description:
        return
    # Trim any starting \n\
    description = description.replace("\n\\", "\n")
    print(description)
    print()


def print_issue(issue: Issue, show_description: bool = False):
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
    identifier = f"{Fore.GREEN}{issue.identifier}{Style.RESET_ALL}"
    title = f"{identifier} - {issue.title} ({status})"
    url = f"{Fore.YELLOW}{issue.url}{Style.RESET_ALL}"
    print(title)
    print()
    if show_description:
        print_description(issue.description)

    print(url)


def print_issues(issues: list[Issue]):
    for issue in issues:
        print_issue(issue)
