from xdg import XDGAppCache

from . import gql
from .models import Issue, User, WorkflowState

APP_CACHE = XDGAppCache("linear")


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
            state {
                id
                name
                type
            }
        }
    }
    """ % (
        id
    )

    def map_issue(issue):
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

    if data := APP_CACHE.load(id):
        return map_issue(data["data"]["issue"])

    data = gql.request(query)
    APP_CACHE.save(id, data)
    return map_issue(data["data"]["issue"])


def get_me() -> User:
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

    def map_issue(issue):
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

    def map_user(viewer):
        return User(
            id=viewer["id"],
            name=viewer["name"],
            email=viewer["email"],
            assigned_issues=[
                map_issue(issue) for issue in viewer["assignedIssues"]["nodes"]
            ],
        )

    if data := APP_CACHE.load(query):
        return map_user(data["data"]["viewer"])
    data = gql.request(query)
    APP_CACHE.save(query, data)

    return map_user(data["data"]["viewer"])
