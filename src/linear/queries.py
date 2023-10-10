from xdg import XDGAppCache

from . import gql
from .models import Issue, User

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
        Issue.gql_fields(),
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
