from dataclasses import dataclass
from typing import Optional

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
    locations: list[dict[str, int]]
    extensions: dict[str, str]

    @staticmethod
    def from_gql(error: dict) -> "LinearErrorMessage":
        return LinearErrorMessage(
            message=error["message"],
            locations=error["locations"],
            extensions=error["extensions"],
        )


@dataclass
class WorkflowState:
    id: str
    name: str
    type: str


@dataclass
class Comment:
    id: str
    body: str
    created_at: str
    user_name: str


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
    children: list["Issue"]
    comments: Optional[list["Comment"]]

    @staticmethod
    def gql_fields(include_children=False) -> str:
        children_query = ""
        if include_children:
            children_query = """
                children {
                    nodes {
                        %s
                    }
                }
            """ % (
                Issue.gql_fields()
            )
        return """
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
            comments {
                nodes {
                    id
                    body
                    createdAt
                    user {
                        name
                    }
                }
            }
            %s
        """ % (
            children_query
        )

    @staticmethod
    def from_gql(issue: dict) -> "Issue":
        has_children = "children" in issue
        return Issue(
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
            children=[Issue.from_gql(child) for child in issue["children"]["nodes"]]
            if has_children
            else [],
            comments=[
                Comment(
                    id=comment["id"],
                    body=comment["body"],
                    created_at=comment["createdAt"],
                    user_name=comment["user"]["name"],
                )
                for comment in issue.get("comments", {}).get("nodes", [])
            ],
        )


@dataclass
class Team:
    id: str
    name: str
    issues: Optional[list[Issue]]

    @staticmethod
    def gql_fields(include_issues=False) -> str:
        if include_issues:
            return """
                id
                name
                issues {
                    nodes {
                        %s
                    }
                }
            """ % (
                Issue.gql_fields(include_children=False)
            )
        else:
            return """
                id
                name
            """

    @staticmethod
    def from_gql(team: dict) -> "Team":
        issues = team.get("issues", {}).get("nodes", [])
        return Team(
            id=team["id"],
            name=team["name"],
            issues=[Issue.from_gql(issue) for issue in issues],
        )


@dataclass
class User:
    id: str
    name: str
    email: str
    assigned_issues: list[Issue]
    """
    Issues assigned to the user.
    """
    teams: list[Team]
    """
    List of teams the user is a member of.
    """

    @staticmethod
    def gql_fields() -> str:
        return """
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
            teamMemberships {
                nodes {
                    team {
                        %s
                    }
                }
            }
        """ % (
            Team.gql_fields(include_issues=False)
        )

    @staticmethod
    def from_gql(viewer: dict) -> "User":
        return User(
            id=viewer["id"],
            name=viewer["name"],
            email=viewer["email"],
            assigned_issues=[
                Issue.from_gql(issue) for issue in viewer["assignedIssues"]["nodes"]
            ],
            teams=[
                Team.from_gql(team["team"])
                for team in viewer["teamMemberships"]["nodes"]
            ],
        )
