import hashlib

from xdg import XDGAppCache

from . import gql
from .models import Issue, Team, User


APP_CACHE = XDGAppCache("linear")


def cache_load(query: str) -> dict | None:
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    return APP_CACHE.load(query_hash)


def cache_save(query: str, data: dict):
    query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
    APP_CACHE.save(query_hash, data)


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

    if data := cache_load(query):
        return Issue.from_gql(data["data"]["issue"])

    data = gql.request(query)
    cache_save(query, data)
    return Issue.from_gql(data["data"]["issue"])


def get_me() -> User:
    query = """
    query Me {
        viewer {
            %s
        }
    }
    """ % (User.gql_fields())

    if data := cache_load(query):
        return User.from_gql(data["data"]["viewer"])
    data = gql.request(query)
    cache_save(query, data)

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
    if data := cache_load(query):
        return Team.from_gql(data["data"]["team"])
    data = gql.request(query)
    cache_save(query, data)
    return Team.from_gql(data["data"]["team"])
