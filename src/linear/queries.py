from xdg import XDGAppCache

from . import gql
from .models import Issue, Team, User

APP_CACHE = XDGAppCache("linear")


def get_issue(id: str) -> Issue:
    query = """
    query Issue {
      issue(id: "%s") {
          %s
        }
    }
    """ % (
        id,
        Issue.gql_fields(include_children=True),
    )

    if data := APP_CACHE.load(id):
        return Issue.from_gql(data["data"]["issue"])

    data = gql.request(query)
    APP_CACHE.save(id, data)
    return Issue.from_gql(data["data"]["issue"])


def get_me() -> User:
    query = """
    query Me {
        viewer {
            %s
        }
    }
    """ % (
        User.gql_fields()
    )

    if data := APP_CACHE.load(query):
        return User.from_gql(data["data"]["viewer"])
    data = gql.request(query)
    APP_CACHE.save(query, data)

    return User.from_gql(data["data"]["viewer"])


def get_team(team_id: str):
    query = """
    query Team {
      team(id: "%s") {
          %s
      }
    }
    """ % (
        team_id,
        Team.gql_fields(include_issues=True),
    )
    if data := APP_CACHE.load(query):
        return Team.from_gql(data["data"]["team"])
    data = gql.request(query)
    APP_CACHE.save(query, data)
    return Team.from_gql(data["data"]["team"])
