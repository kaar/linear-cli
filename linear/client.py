from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests

from .cache import Cache

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
    def from_dict(cls, state: dict) -> WorkflowState:
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
class Attachment:
    """
    External resources attached to an issue like GitHub PRs or Slack threads.
    Shown as links in the Linear UI.
    """

    id: str
    title: str
    url: str
    source_type: str

    @classmethod
    def from_dict(cls, attachment: dict) -> "Attachment":
        return cls(
            id=attachment["id"],
            title=attachment["title"],
            url=attachment["url"],
            source_type=attachment["sourceType"],
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
    children: list[Issue]
    comments: Optional[list[Comment]]
    assignee: Optional[User] = None
    attachments: Optional[list[Attachment]] = None

    @classmethod
    def from_dict(cls, issue: dict) -> Issue:
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
            attachments=[
                Attachment.from_dict(attachment)
                for attachment in issue.get("attachments", {}).get("nodes", [])
            ],
        )


@dataclass
class Team:
    id: str
    name: str
    issues: list[Issue]

    @classmethod
    def from_dict(cls, data: dict) -> Team:
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
    def from_dict(cls, user: dict) -> User:
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


class LinearClient:
    def __init__(
        self,
        url: str,
        api_key: str,
        cache: Cache,
    ):
        self._base_url = url
        self._api_key = api_key
        self._session = requests.Session()
        self._cache = cache

    def get_me(self) -> User:
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
        data = self._gql_request(query)
        return User.from_dict(data["data"]["viewer"])

    def get_issue(self, issue_id: str) -> Issue:
        query = """
        query GetIssue($issue_id: String!) {
            issue(id: $issue_id) {
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
                attachments {
                    nodes {
                        id
                        title
                        url
                        sourceType
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
        """
        data = self._gql_request(query, issue_id=issue_id)
        return Issue.from_dict(data["data"]["issue"])

    def get_team(self, team_id: str) -> Team:
        query = """
        query GetTeam($team_id: String!) {
            team(id: $team_id) {
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
        """
        gql_data = self._gql_request(query, team_id=team_id)["data"]
        return Team.from_dict(gql_data)

    def _gql_request(self, query: str, **variables) -> dict:
        """
        Send a GraphQL query to Linear and return the response as a dictionary.
        Args:
            query (str): The GraphQL query to send to Linear.
        Returns:
            dict: The response from Linear.
        Raises:
            LinearRequestError: If the query was invalid.
        """
        if data := self._cache.get(query):
            return data
        response = self._session.post(
            self._base_url,
            headers={"Authorization": self._api_key},
            json={"query": query, "variables": variables},
        )
        data = response.json()
        if "errors" in data:
            raise LinearRequestError(
                [LinearErrorMessage.from_gql(error) for error in data["errors"]]
            )
        self._cache.set(query, data)
        return data
