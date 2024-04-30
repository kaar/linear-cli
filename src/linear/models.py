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
    extensions: dict[str, str]
    locations: Optional[list[dict[str, int]]] = None

    @staticmethod
    def from_gql(error: dict) -> "LinearErrorMessage":
        return LinearErrorMessage(
            message=error["message"],
            extensions=error["extensions"],
            locations=error.get("locations"),
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
    assignee: Optional["User"] = None

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
                }
            }
            %s
        """ % (
            children_query
        )

    @staticmethod
    def from_gql(issue: dict) -> "Issue":
        has_children = "children" in issue
        has_assignee = "assignee" in issue and issue["assignee"] is not None
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
            assignee=User.from_gql(issue["assignee"]) if has_assignee else None,
        )


@dataclass
class Team:
    id: str
    name: str
    issues: list[Issue]

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
    teams: Optional[list[Team]] = None
    """
    List of teams the user is a member of.
    """

    assigned_issues: Optional[list[Issue]] = None
    """
    Issues assigned to the user.
    """

    @staticmethod
    def gql_fields() -> str:
        return """
            id
            name
            email
            teamMemberships {
                nodes {
                    team {
                        %s
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
        """ % (
            Team.gql_fields(include_issues=False)
        )

    @staticmethod
    def from_gql(viewer: dict) -> "User":
        has_assigned_issues = "assignedIssues" in viewer
        has_teams = "teamMemberships" in viewer
        return User(
            id=viewer["id"],
            name=viewer["name"],
            email=viewer["email"],
            teams=[
                Team.from_gql(team["team"])
                for team in viewer["teamMemberships"]["nodes"]
            ]
            if has_teams
            else None,
            assigned_issues=[
                Issue.from_gql(issue) for issue in viewer["assignedIssues"]["nodes"]
            ]
            if has_assigned_issues
            else None,
        )
