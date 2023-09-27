import os
from dataclasses import dataclass
from pathlib import Path

import requests

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
QUERY_PATH = Path(__file__).parent / "queries"


@dataclass
class Issue:
    id: str
    title: str
    description: str


def load_query(filename: str) -> str:
    file_path = QUERY_PATH / filename
    with open(file_path, "r") as f:
        return f.read()


def get_issue(issue_id: str) -> Issue:
    query = (load_query("get_issue.graphql")) % issue_id

    response = requests.post(
        "https://api.linear.app/graphql",
        headers={"Authorization": LINEAR_API_KEY},
        json={"query": query},
    )

    return Issue(**response.json()["data"]["issue"])


def main():
    issue = get_issue("TRA-383")
    print(issue.id)
    print(issue.title)
    print(issue.description)


def cli():
    main()


if __name__ == "__main__":
    main()
