from dataclasses import dataclass


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

    @staticmethod
    def gql_fields() -> str:
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
        """

    @staticmethod
    def from_gql(issue: dict) -> "Issue":
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

    @staticmethod
    def gql_fields() -> str:
        return """
            id
            name
            email
            assignedIssues {
                nodes {
                    %s
                }
            }
        """ % (
            Issue.gql_fields()
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
        )
