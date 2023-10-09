import os

import requests

from .models import LinearErrorMessage

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
LINEAR_URL = "https://api.linear.app/graphql"


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


def request(query: str) -> dict:
    """
    Send a GraphQL query to Linear and return the response.

    Args:
        query (str): The GraphQL query to send to Linear.

    Returns:
        dict: The response from Linear.

    Raises:
        LinearRequestError: If the query was invalid.
    """
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

    return data
