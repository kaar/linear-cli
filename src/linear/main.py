import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path

import requests

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
QUERY_PATH = Path(__file__).parent / "queries"


@dataclass
class Assignee:
    id: str
    name: str


@dataclass
class Node:
    id: str
    title: str
    description: str
    description: str
    assignee: str
    createdAt: str
    archivedAt: str


@dataclass
class Issue:
    id: str
    title: str
    description: str


@dataclass
class Project:
    id: str


@dataclass
class User:
    id: str
    name: str
    email: str


@dataclass
class Team:
    id: str
    name: str


def load_query(filename: str) -> str:
    file_path = QUERY_PATH / filename
    with open(file_path, "r") as f:
        return f.read()


def graphql_request(query: str) -> dict:
    response = requests.post(
        "https://api.linear.app/graphql",
        headers={"Authorization": LINEAR_API_KEY},
        json={"query": query},
    )

    return response.json()


def get_issue(issue_id: str) -> Issue:
    data = graphql_request(load_query("get_issue.graphql") % issue_id)
    return Issue(**data["data"]["issue"])


def get_project(project_id: str) -> Project:
    data = graphql_request(load_query("get_project.graphql") % project_id)
    return Project(**data["data"]["project"])


def get_me() -> User:
    data = graphql_request(load_query("get_me.graphql"))
    return User(**data["data"]["viewer"])


def get_teams() -> list[Team]:
    data = graphql_request(load_query("get_teams.graphql"))
    return [Team(**team) for team in data["data"]["teams"]["nodes"]]


def get_team(team_id: str) -> Team:
    data = graphql_request(load_query("get_team.graphql") % team_id)
    print(json.dumps(data, indent=2))
    return None


def main():
    issue = get_issue("TRA-383")
    print(issue.id)
    print(issue.title)
    print(issue.description)

    me = get_me()
    print(me.id)
    print(me.name)
    print(me.email)

    teams = get_teams()

    for team in teams:
        # print(team.id)
        print(team.name)

    trading_team = [team for team in teams if team.name == "Trading"][0]

    team = get_team(trading_team.id)

    print(team)

    # project = get_project()
    # print(project.id)
    # print(project.name)


def issue_list():
    query = """
    query {
        issues {
            nodes {
                id
                title
                description
            }
        }
    }
    """

    response = graphql_request(query)

    for issue in response["data"]["issues"]["nodes"]:
        print(issue["title"])


def cli():
    # linear issue list
    # linear issue view <issue_id>

    # Examples:
    # linear issue view TRA-331

    # linear project list
    # linear project view <project_id>

    # linear team list
    # linear team view <team_id>

    parser = argparse.ArgumentParser(description="Linear CLI")

    parser.add_argument("command", help="The command to run")

    args = parser.parse_args()

    if args.command == "issue":
        issue_list()


if __name__ == "__main__":
    main()
