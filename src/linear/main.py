import os

import requests


def main():
    LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]

    query = """
    query Issue {
      issue(id: "TRA-383") {
        id
        title
        description
      }
    }
    """

    response = requests.post(
        "https://api.linear.app/graphql",
        headers={"Authorization": LINEAR_API_KEY},
        json={"query": query},
    )

    print(response.status_code)
    print(response.json())
    json_data = response.json()

    print(json_data["data"]["issue"]["title"])


def cli():
    print("Hello world from cli")


if __name__ == "__main__":
    main()
