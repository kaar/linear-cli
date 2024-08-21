import json
import os
import time
import hashlib
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

ISSUE_STATES = [
    "backlog",
    "completed",
    "started",
    "unstarted",
    "canceled",
]


@dataclass
class LinearErrorMessage:
    message: str
    extensions: dict[str, str]
    locations: Optional[list[dict[str, int]]] = None

    @classmethod
    def from_gql(cls, error: dict) -> "LinearErrorMessage":
        return cls(
            message=error["message"],
            extensions=error["extensions"],
            locations=error.get("locations"),
        )


class LinearRequestError(Exception):
    def __init__(self, error_messages: list[LinearErrorMessage]):
        self.error_messages = error_messages

    def __str__(self):
        error_messages = "\n".join(
            [
                f"- {error_message.message} (line {error_message.locations[0]['line']})"
                for error_message in self.error_messages
            ]
        )
        return "\n" + error_messages


@dataclass
class WorkflowState:
    id: str
    name: str
    type: str

    @classmethod
    def from_dict(cls, state: dict) -> "WorkflowState":
        return cls(
            id=state["id"],
            name=state["name"],
            type=state["type"],
        )


@dataclass
class Comment:
    id: str
    body: str
    created_at: datetime
    user_name: Optional[str] = None
    parent_id: Optional[str] = None

    @classmethod
    def from_dict(cls, comment: dict) -> "Comment":
        return cls(
            id=comment["id"],
            body=comment["body"],
            created_at=datetime.fromisoformat(comment["createdAt"]),
            user_name=comment["user"]["name"] if comment["user"] else None,
            parent_id=comment["parent"]["id"] if comment["parent"] else None,
        )


@dataclass
class Issue:
    id: str
    identifier: str
    """Issue's human readable identifier (e.g. ENG-123)."""
    title: str
    """The issue's title."""
    description: str
    created_at: str
    url: str
    state: WorkflowState
    children: list["Issue"]
    comments: Optional[list["Comment"]]
    assignee: Optional["User"] = None

    @classmethod
    def from_dict(cls, issue: dict) -> "Issue":
        has_children = "children" in issue
        has_assignee = "assignee" in issue and issue["assignee"] is not None
        return cls(
            id=issue["id"],
            identifier=issue["identifier"],
            title=issue["title"],
            description=issue["description"],
            created_at=issue["createdAt"],
            url=issue["url"],
            state=WorkflowState.from_dict(issue["state"]),
            children=(
                [Issue.from_dict(child) for child in issue["children"]["nodes"]]
                if has_children
                else []
            ),
            comments=[
                Comment.from_dict(comment)
                for comment in issue.get("comments", {}).get("nodes", [])
            ],
            assignee=User.from_dict(issue["assignee"]) if has_assignee else None,
        )


@dataclass
class Team:
    id: str
    name: str
    issues: list[Issue]

    @classmethod
    def from_dict(cls, data: dict) -> "Team":
        team = data["team"]
        issues = team.get("issues", {}).get("nodes", [])
        return cls(
            id=team["id"],
            name=team["name"],
            issues=[Issue.from_dict(issue) for issue in issues],
        )


@dataclass
class User:
    id: str
    name: str
    email: str
    teams: Optional[list[Team]] = None
    """List of teams the user is a member of."""
    assigned_issues: Optional[list[Issue]] = None
    """Issues assigned to the user."""

    @classmethod
    def from_dict(cls, user: dict) -> "User":
        has_assigned_issues = "assignedIssues" in user
        has_teams = "teamMemberships" in user
        return cls(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            teams=(
                [Team.from_dict(team) for team in user["teamMemberships"]["nodes"]]
                if has_teams
                else None
            ),
            assigned_issues=(
                [Issue.from_dict(issue) for issue in user["assignedIssues"]["nodes"]]
                if has_assigned_issues
                else None
            ),
        )


LINEAR_URL = "https://api.linear.app/graphql"
LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
LINEAR_CACHE_PATH = Path(
    os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"), "linear"
)


def query_cache_file(query: str) -> Path:
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    return Path(LINEAR_CACHE_PATH, f"{query_hash}.json")


def query_cache_load(query: str, ttl: int = 30) -> dict | None:
    cache_file = query_cache_file(query)
    if not cache_file.exists():
        return None
    creation_time = cache_file.stat().st_mtime
    if time.time() - creation_time > ttl:
        cache_file.unlink()
        return None
    return json.loads(cache_file.read_text())


def query_cache_dump(query: str, data: dict):
    cache_file = query_cache_file(query)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data))


def gql_request(query: str) -> dict:
    """
    Send a GraphQL query to Linear and return the response as a dictionary.
    Args:
        query (str): The GraphQL query to send to Linear.
    Returns:
        dict: The response from Linear.
    Raises:
        LinearRequestError: If the query was invalid.
    """
    if data := query_cache_load(query):
        return data
    response = requests.post(
        LINEAR_URL,
        headers={"Authorization": LINEAR_API_KEY},
        json={"query": query},
    )
    data = response.json()
    if "errors" in data:
        raise LinearRequestError(
            [LinearErrorMessage.from_gql(error) for error in data["errors"]]
        )
    query_cache_dump(query, data)
    return data


def get_team(team_id: str) -> Team:
    query = """
    query Team {
        team(id: "%s") {
            id
            name
            issues {
                nodes {
                    id
                    identifier
                    title
                    createdAt
                    description
                    url
                    assignee {
                        id
                        name
                        email
                    }
                    state {
                        id
                        name
                        type
                    }
                }
            }
        }
    }
    """ % (team_id)
    gql_data = gql_request(query)["data"]
    return Team.from_dict(gql_data)


def get_issue(id: str) -> Issue:
    query = """
    query Issue {
      issue(id: "%s") {
            id
            identifier
            title
            createdAt
            description
            url
            assignee {
                id
                name
                email
            }
            state {
              id
              name
              type
            }
            comments {
                nodes {
                    id
                    body
                    createdAt
                    user {
                        name
                    }
                    parent {
                        id
                    }
                }
            }
            children {
                nodes {
                    id
                    identifier
                    title
                    createdAt
                    description
                    url
                    assignee {
                        id
                        name
                        email
                    }
                    state {
                      id
                      name
                      type
                    }
                }
            }
        }
    }
    """ % (id)
    data = gql_request(query)
    return Issue.from_dict(data["data"]["issue"])


def get_me() -> User:
    query = """
    query Me {
        viewer {
            id
            name
            email
            teamMemberships {
                nodes {
                    team {
                        id
                        name
                    }
                }
            }
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
    data = gql_request(query)
    return User.from_dict(data["data"]["viewer"])
