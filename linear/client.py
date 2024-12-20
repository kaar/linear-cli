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
        print(data["errors"])
        raise LinearRequestError(
            [LinearErrorMessage.from_gql(error) for error in data["errors"]]
        )
    query_cache_dump(query, data)
    return data


def get_team(team_id: str) -> Team:
    query = f"""
    query Team {{
        team(id: "{team_id}") {{
            id
            name
            issues {{
                nodes {{
                    id
                    identifier
                    title
                    createdAt
                    description
                    url
                    assignee {{
                        id
                        name
                        email
                    }}
                    state {{
                        id
                        name
                        type
                    }}
                }}
            }}
        }}
    }}
    """
    gql_data = gql_request(query)["data"]
    return Team.from_dict(gql_data)


#
# type Query {
#   """
#   One specific project milestone.
#   """
#   ProjectMilestone(id: String!): ProjectMilestone!
#   """
#   All milestones for the project.
#   """
#   ProjectMilestones(
#     """
#     A cursor to be used with first for forward pagination
#     """
#     after: String
#     """
#     A cursor to be used with last for backward pagination.
#     """
#     before: String
#     """
#     The number of items to forward paginate (used with after). Defaults to 50.
#     """
#     first: Int
#     """
#     Should archived resources be included (default: false)
#     """
#     includeArchived: Boolean
#     """
#     The number of items to backward paginate (used with before). Defaults to 50.
#     """
#     last: Int
#     """
#     By which field should the pagination order by. Available options are createdAt (default) and updatedAt.
#     """
#     orderBy: PaginationOrderBy
#   ): ProjectMilestoneConnection!
#   """
#   All teams you the user can administrate. Administrable teams are teams whose settings the user can change, but to whose issues the user doesn't necessarily have access to.
#   """
#   administrableTeams(
#     """
#     A cursor to be used with first for forward pagination
#     """
#     after: String
#     """
#     A cursor to be used with last for backward pagination.
#     """
#     before: String
#     """
#     Filter returned teams.
#     """
#     filter: TeamFilter
#     """
#     The number of items to forward paginate (used with after). Defaults to 50.
#     """
#     first: Int
#     """
#     Should archived resources be included (default: false)
#     """
#     includeArchived: Boolean
#     """
#     The number of items to backward paginate (used with before). Defaults to 50.
#     """
#     last: Int
#     """
#     By which field should the pagination order by. Available options are createdAt (default) and updatedAt.
#     """
#     orderBy: PaginationOrderBy
#   ): TeamConnection!
#   """
#   All API keys for the user.
#   """
#   apiKeys(
#     """
#     A cursor to be used with first for forward pagination
#     """
#     after: String
#     """
#     A cursor to be used with last for backward pagination.
#     """
#     before: String
#     """
#     The number of items to forward paginate (used with after). Defaults to 50.
#     """
#     first: Int
#     """
#     Should archived resources be included (default: false)
#     """
#     includeArchived: Boolean
#     """
#     The number of items to backward paginate (used with before). Defaults to 50.
#     """
#     last: Int
#     """
#     By which field should the pagination order by. Available options are createdAt (default) and updatedAt.
#     """
#     orderBy: PaginationOrderBy
#   ): ApiKeyConnection!
#   """
#   Get basic information for an application.
#   """
#   applicationInfo(
#     """
#     The client ID of the application.
#     """
#     clientId: String!
#   ): Application!
#   """
#   [INTERNAL] Get basic information for a list of applications
#   """
#   applicationInfoByIds(
#     """
#     The IDs of the applications.
#     """
#     ids: [String!]!
#   ): [Application!]!
#   """
#   Get information for an application and whether a user has approved it for the given scopes.
#   """
#   applicationWithAuthorization(
#     """
#     Actor mode used for the authorization.
#     """
#     actor: String = "user"
#     """
#     The client ID of the application.
#     """
#     clientId: String!
#     """
#     Redirect URI for the application.
#     """
#     redirectUri: String
#     """
#     Scopes being requested by the application
#     """
#     scope: [String!]!
#   ): UserAuthorizedApplication!
#   """
#   One specific issue attachment.
#   [Deprecated] 'url' can no longer be used as the 'id' parameter. Use 'attachmentsForUrl' instead
#   """
#   attachment(id: String!): Attachment!
#   """
#   Query an issue by its associated attachment, and its id.
#   """
#   attachmentIssue(
#     """
#     `id` of the attachment for which you'll want to get the issue for. [Deprecated] `url` as the `id` parameter.
#     """
#     id: String!
#   ): Issue!
#     @deprecated(
#       reason: "Will be removed in near future, please use `attachmentsForURL` to get attachments and their issues instead."
#     )
#   """
#   All issue attachments.
#
#   To get attachments for a given URL, use `attachmentsForURL` query.
#   """
#   attachments(
#     """
#     A cursor to be used with first for forward pagination
#     """
#     after: String
#     """
#     A cursor to be used with last for backward pagination.
#     """
#     before: String
#     """
#     Filter returned attachments.
#     """
#     filter: AttachmentFilter
#     """
#     The number of items to forward paginate (used with after). Defaults to 50.
#     """
#     first: Int
#     """
#     Should archived resources be included (default: false)
#     """
#     includeArchived: Boolean
#     """
#     The number of items to backward paginate (used with before). Defaults to 50.
#     """
#     last: Int
#     """
#     By which field should the pagination order by. Available options are createdAt (default) and updatedAt.
#     """
#     orderBy: PaginationOrderBy
#   ): AttachmentConnection!
#   """
#   Returns issue attachments for a given `url`.
#   """
#   attachmentsForURL(
#     """
#     A cursor to be used with first for forward pagination
#     """
#     after: String
#     """
#     A cursor to be used with last for backward pagination.
#     """
#     before: String
#     """
#     The number of items to forward paginate (used with after). Defaults to 50.
#     """
#     first: Int
#     """
#     Should archived resources be included (default: false)
#     """
#     includeArchived: Boolean
#     """
#     The number of items to backward paginate (used with before). Defaults to 50.
#     """
#     last: Int
#     """
#     By which field should the pagination order by. Available options are createdAt (default) and updatedAt.
#     """
#     orderBy: PaginationOrderBy
#     """
#     The attachment URL.
#     """
#     url: String!
#   ): AttachmentConnection!
#   """
#   All audit log entries.
#   """
#   auditEntries(
#     """
#     A cursor to be used with first for forward pagination
#     """
#     after: String
#     """
#     A cursor to be used with last for backward pagination.
#     """
#     before: String
#     """
#     Filter returned audit entries.
#     """
#     filter: AuditEntryFilter
#     """
#     The number of items to forward paginate (used with after). Defaults to 50.
#     """
#     first: Int
#     """
#     Should archived resources be included (default: false)
#     """
#     includeArchived: Boolean
#     """
#     The number of items to backward paginate (used with before). Defaults to 50.
#     """
#     last: Int
#     """
#     By which field should the pagination order by. Available options are createdAt (default) and updatedAt.
#     """
#     orderBy: PaginationOrderBy
#   ): AuditEntryConnection!
#   """
#   List of audit entry types.
#   """
#   auditEntryTypes: [AuditEntryType!]!
#   """
#   [INTERNAL] Get all authorized applications for a user
#   """
#   authorizedApplications: [AuthorizedApplication!]!
#   """
#   Fetch users belonging to this user account.
#   """
#   availableUsers: AuthResolverResponse!
#   """
#   A specific comment.
#   """
#   comment(
#     """
#     The identifier of the comment to retrieve.
#     """
#     id: String!
#   ): Comment!
#   """
#   All comments.
#   """
#   comments(
#     """
#     A cursor to be used with first for forward pagination
#     """
#     after: String
#     """
#     A cursor to be used with last for backward pagination.
#     """
#     before: String
#     """
#     Filter returned comments.
#     """
#     filter: CommentFilter
#     """
#     The number of items to forward paginate (used with after). Defaults to 50.
#     """
#     first: Int
#     """
#     Should archived resources be included (default: false)
#     """
#     includeArchived: Boolean
#     """
#     The number of items to backward paginate (used with before). Defaults to 50.
#     """
#     last: Int
#     """
#     By which field should the pagination order by. Available options are createdAt (default) and updatedAt.
#     """
#     orderBy: PaginationOrderBy
#   ): CommentConnection!
#   """
#   One specific custom view.
#   """
#   customView(id: String!): CustomView!
#   """
#   Custom views for the user.
#   """
#   customViews(
#     """
#     A cursor to be used with first for forward pagination
#     """
#     after: String
#     """
#     A cursor to be used with last for backward pagination.
#     """
#     before: String
#     """
#     The number of items to forward paginate (used with after). Defaults to 50.
#     """
#     first: Int
#     """
#     Should archived resources be included (default: false)
#     """
#     includeArchived: Boolean
#     """
#     The number of items to backward paginate (used with before). Defaults to 50.
#     """
#     last: Int
#     """
#     By which field should the pagination order by. Available options are createdAt (default) and updatedAt.
#     """
#     orderBy: PaginationOrderBy
#   ): CustomViewConnection!
#


def get_custom_views() -> list[dict]:
    query = """
    query CustomViews {
        customViews {
            nodes {
                id
                name
                filters
            }
        }
    }
    """
    print(json.dumps(gql_request(query), indent=2))
    data = gql_request(query)
    return data["data"]["customViews"]["nodes"]


# """
# A custom view that has been saved by a user.
# """
# type CustomView implements Node {
#   """
#   The time at which the entity was archived. Null if the entity has not been archived.
#   """
#   archivedAt: DateTime
#   """
#   The color of the icon of the custom view.
#   """
#   color: String
#   """
#   The time at which the entity was created.
#   """
#   createdAt: DateTime!
#   """
#   The user who created the custom view.
#   """
#   creator: User!
#   """
#   The description of the custom view.
#   """
#   description: String
#   """
#   The filter applied to issues in the custom view.
#   """
#   filterData: JSONObject!
#   """
#   The filters applied to issues in the custom view.
#   """
#   filters: JSONObject! @deprecated(reason: "Will be replaced by `filterData` in a future update")
#   """
#   The icon of the custom view.
#   """
#   icon: String
#   """
#   The unique identifier of the entity.
#   """
#   id: ID!
#   """
#   The name of the custom view.
#   """
#   name: String!
#   """
#   The organization of the custom view.
#   """
#   organization: Organization!
#   """
#   Whether the custom view is shared with everyone in the organization.
#   """
#   shared: Boolean!
#   """
#   The team associated with the custom view.
#   """
#   team: Team
#   """
#   The last time at which the entity was meaningfully updated, i.e. for all changes of syncable properties except those
#       for which updates should not produce an update to updatedAt (see skipUpdatedAtKeys). This is the same as the creation time if the entity hasn't
#       been updated after creation.
#   """
#   updatedAt: DateTime!
# }


# """
# The user's favorites.
# """
# favorites(
#   """
#   A cursor to be used with first for forward pagination
#   """
#   after: String
#   """
#   A cursor to be used with last for backward pagination.
#   """
#   before: String
#   """
#   The number of items to forward paginate (used with after). Defaults to 50.
#   """
#   first: Int
#   """
#   Should archived resources be included (default: false)
#   """
#   includeArchived: Boolean
#   """
#   The number of items to backward paginate (used with before). Defaults to 50.
#   """
#   last: Int
#   """
#   By which field should the pagination order by. Available options are createdAt (default) and updatedAt.
#   """
#   orderBy: PaginationOrderBy
# ): FavoriteConnection!


# """
# The favorited custom view.
# """
# customView: CustomView
def get_favorites() -> list[dict]:
    query = """
    query Favorites {
        favorites {
            nodes {
                id
                createdAt
                customView {
                    name
                    filterData
                }
                project {
                    name
                }
            }
        }
    }
    """
    data = gql_request(query)
    print(json.dumps(data, indent=2))
    return data["data"]["favorites"]["nodes"]


def get_triage_issues(team_id) -> list[Issue]:

    query = f"""
    query Team {{
        team(id: "{team_id}") {{
            id
            name
            issues {{
                nodes {{
                    id
                    identifier
                    title
                    createdAt
                    description
                    url
                    assignee {{
                        id
                        name
                        email
                    }}
                    state {{
                        id
                        name
                        type
                    }}
                }}
            }}
        }}
    }}
    """
    query = """
    query
    }
    """
    data = gql_request(query)
    print(data)
    print(json.dumps(data, indent=2))
    return [Issue.from_dict(issue) for issue in data["data"]["issues"]["nodes"]]


def get_issue(id: str) -> Issue:
    query = f"""
    query Issue {{
        issue(id: "{id}") {{
            id
            identifier
            title
            createdAt
            description
            url
            assignee {{
                id
                name
                email
            }}
            state {{
                id
                name
                type
            }}
            comments {{
                nodes {{
                    id
                    body
                    createdAt
                    user {{
                        name
                    }}
                    parent {{
                        id
                    }}
                }}
            }}
            children {{
                nodes {{
                    id
                    identifier
                    title
                    createdAt
                    description
                    url
                    assignee {{
                        id
                        name
                        email
                    }}
                    state {{
                        id
                        name
                        type
                    }}
                }}
            }}
        }}
    }}
    """
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
