import os

import requests

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
LINEAR_URL = "https://api.linear.app/graphql"


def request(query: str) -> dict:
    response = requests.post(
        LINEAR_URL,
        headers={"Authorization": LINEAR_API_KEY},
        json={"query": query},
    )
    return response.json()
