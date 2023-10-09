import os
from dataclasses import dataclass

import requests

from .xdg import XDGAppCache

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
LINEAR_URL = "https://api.linear.app/graphql"


APP_CACHE = XDGAppCache("linear")


def gql_request(query: str) -> dict:
    if response := APP_CACHE.load(query):
        return response

    response = requests.post(
        LINEAR_URL,
        headers={"Authorization": LINEAR_API_KEY},
        json={"query": query},
    )

    APP_CACHE.save(query, response.json())

    return response.json()


@dataclass
class WorkflowState:
    id: str
    name: str
    type: str


@dataclass
class Issue:
    id: str

    identifier: str
    """
    Issue's human readable identifier (e.g. ENG-123).
    """

    title: str
    """
    The issue's title.
    """

    description: str
    created_at: str
    url: str
    state: WorkflowState


@dataclass
class User:
    id: str
    name: str
    email: str
    assigned_issues: list[Issue]
    """
    Issues assigned to the user.
    """


@dataclass
class Team:
    id: str
    name: str


def get_issue(id: str) -> Issue:
    query = """
    query Issue {
      issue(id: "%s") {
        id
        title
        description
        url
      }
    }
    """ % (
        id
    )
    data = gql_request(query)
    return Issue(**data["data"]["issue"])


class LinearClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def gql_request(self, query: str) -> dict:
        return gql_request(query)

    def get_me(self) -> User:
        query = """
        query Me {
          viewer {
            id
            name
            email
            assignedIssues {
                nodes {
                    id
                    identifier
                    title
                    createdAt
                    description
                    url
                    state {
                        id
                        name
                        type
                    }
                }
            }
          }
        }
        """
        data = self.gql_request(query)
        viewer = data["data"]["viewer"]
        user = User(
            id=viewer["id"],
            name=viewer["name"],
            email=viewer["email"],
            assigned_issues=[
                Issue(
                    id=issue["id"],
                    identifier=issue["identifier"],
                    title=issue["title"],
                    description=issue["description"],
                    created_at=issue["createdAt"],
                    url=issue["url"],
                    state=WorkflowState(
                        id=issue["state"]["id"],
                        name=issue["state"]["name"],
                        type=issue["state"]["type"],
                    ),
                )
                for issue in viewer["assignedIssues"]["nodes"]
            ],
        )
        return user

    def get_issue(self, id: str) -> Issue:
        query = """
        query Issue {
          issue(id: "%s") {
            id
            title
            description
          }
        }
        """ % (
            id
        )
        data = self.gql_request(query)
        return Issue(**data["data"]["issue"])

    def get_teams(self):
        query = """
        query Teams {
          teams {
            nodes {
              id
              name
            }
          }
        }
        """
        data = self.gql_request(query)
        return [Team(**team) for team in data["data"]["teams"]["nodes"]]


def main():
    client = LinearClient(LINEAR_API_KEY)
    me = client.get_me()
    print(f"Hello {me.name}! Your email is {me.email}")

    issue = client.get_issue("TRA-383")
    print(f"Found issue {issue.title} with description {issue.description}")

    teams = client.get_teams()
    print(f"Found {len(teams)} teams")


if __name__ == "__main__":
    main()
