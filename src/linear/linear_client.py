import json
import os
from dataclasses import dataclass

import requests

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
LINEAR_URL = "https://api.linear.app/graphql"


def gql_request(query: str) -> dict:
    response = requests.post(
        LINEAR_URL,
        headers={"Authorization": LINEAR_API_KEY},
        json={"query": query},
    )

    return response.json()


# {
#   "id": "5e951b44-48f8-4335-b84c-914d2531f209",
#   "name": "Caspar Nettelbladt",
#   "email": "caspar@tibber.com",
#   "assignedIssues": {
#     "nodes": [
#       {
#         "id": "9da4ddf2-ea29-4b86-bbc7-da6bce17ef73",
#         "title": "Upgrade to airflow 2.6 to solve (?!) queued tasks issues",
#         "description": null
#       },
#       {
#         "id": "51d7ba16-f057-420f-b955-6716b7227124",
#         "title": "Build GR deploy pipelines",
#         "description": null
#       },
#       {
#         "id": "99fb113d-bc2f-48c5-b2b5-fcad7170fa6b",
#         "title": "Use new Charger implementation in FCR-D delivery",
#         "description": "* Use new Charger when creating fleets\n* Add DeviceType.Zaptec in get_available_capacity job\n* Run an FCR-D activation with new implementation (No bidding)"
#       },
#       {
#         "id": "c2610806-9eb4-4e4a-b09c-b6816121e709",
#         "title": "Multiple ramped up events",
#         "description": "We need a solution that ensures that [this condition](https://github.com/tibber/tibber-pyDemandResponse/blob/master/src/devices/chargers.py#L791) is only satisfied once per command.\n\nIn the old Easee implementation, this was done via setting the [command.ramped_start_at](https://github.com/tibber/tibber-pyDemandResponse/blob/master/src/devices/easee.py#L757) attribute and returning in the check if it [is not None](https://github.com/tibber/tibber-pyDemandResponse/blob/master/src/devices/easee.py#L696).\n\nBecause we continuously run this check and satisfy this condition we have multiple Ramped up events for the same command (with ever increasing reaction times)\n\n![image.png](https://uploads.linear.app/9cf35102-320f-4c90-b939-9177ad8e0266/3e842d09-55e4-401d-9e74-0d18f0ad17e2/9fe5870a-79e6-495b-a8d3-91e6f2dd5cb0)\n\nThis is similar for the off command checks."
#       },
#       {
#         "id": "2c5726a6-c4b5-4851-9d74-66f27f2e6dbe",
#         "title": "Grid rewards service to emit GR Events for Rating to consume",
#         "description": "Once the GR service knows a given GR event has \"been fulfilled\", eg. after it was scheduled and we confirm it's happened as planned, the GR service needs to let Rating (and vicariously Wallet) know what we owe the customer. \n\nWe've agreed with @dan and @husky that a first iteration of that interface should involve the GR service emitting SNS events that look like this:\n\n```\nhome_id: <uuid>\nevents: [\n\u00a0\u00a0{\n\u00a0\u00a0\u00a0\u00a0hour: <iso-timestamp>,\n\u00a0\u00a0\u00a0\u00a0reward: 20,\n\u00a0\u00a0\u00a0\u00a0compensation: 90, // actual trade must\u2019ve made 90+20+20\n\u00a0\u00a0\u00a0\u00a0tibber_gain: 20,\n\u00a0\u00a0\u00a0\u00a0currency: \"SEK\",\n\u00a0\u00a0\u00a0\u00a0volume_kwh: 1,\n\u00a0\u00a0\u00a0\u00a0reference: <uuid>,\n    device_id: <uuid>,\n\u00a0\u00a0},\n\n\u00a0\u00a0...\n\n]\n```"
#       },
#       {
#         "id": "6a5da469-5f53-4e9e-b64f-d19d97cb44d3",
#         "title": "Upgrade Airflow 2.2.1 -> 2.5.1",
#         "description": "### Summary\n\nThe current Airflow setup is encountering issues due to a transitive dependency, cython, which upon releasing a new version broke a dependent library, pyyaml. This caused the breakage of the CI, posing risks to the prod deployment. The challenge lies in resolving the breakage without causing a potential crash in the production environment.\n\nAWS manages Airflow for Tibber through the MWAA service, including the installation of a long list of default dependencies, which we replicate. The issue now is that the AWS-managed dependencies are outside of our control and any changes to them, such as upgrading pyyaml, are not possible.\n\nThree options were considered:\n\n1. Bump PyYAML in dependency list. This would fix the CI but cause different PyYAML versions to run in CI and MWAA, which can lead to unexpected breakages.\n2. Pin the problematic transitive dependency, cython.\n3. Upgrade (Airflow) MWAA. \n\nThe consensus is to upgrade Airflow. This would involve setting up a new Airflow prod cluster, modifying bash scripts, verifying the new cluster's functionality, migrating DAGs from the old to the new cluster, and finally deleting the old cluster.\n\n### Task\n\n1. Duplicate and update the existing Terraform setup.\n   1. New naming standard. forecaster-airflow<version>\n\n      Example: forecaster-airflow2.5.1\n2. Create a new instance and upgrade Airflow.\n3. Modify the bash scripts in the forecaster repo to only the new clusters.\n4. Test the new cluster to ensure it functions as expected.\n5. Gradually turn off DAGs in the old cluster, simultaneously turning them on in the new one.\n6. After a successful migration, delete the old cluster.\n7. Monitor the new setup for any issues and fix them as they occur.\n\n**NB**: As we upgrade Airflow, we will be moving from Python 3.7 to 3.10, which will require some minor code updates. Care should be taken to prevent any naming conflicts during the process. There's no urgent deadline for this task, so it can be done with ample testing and care.\n\n### Terraform\n\n[https://github.com/tibber/tibber-terraform-infra-live/tree/main/dev_legacy/eu-west-1/services/forecaster](https://github.com/tibber/tibber-terraform-infra-live/tree/main/dev_legacy/eu-west-1/services/forecaster)\n[https://github.com/tibber/tibber-terraform-infra-live/tree/main/prod_legacy/eu-west-1/services/forecaster](https://github.com/tibber/tibber-terraform-infra-live/tree/main/prod_legacy/eu-west-1/services/forecaster)\n\n### Resources\n\n[https://docs.aws.amazon.com/mwaa/latest/userguide/airflow-versions.html](https://docs.aws.amazon.com/mwaa/latest/userguide/airflow-versions.html)\n\n[Slack thread](https://tibber.slack.com/archives/C01GXPWK2LS/p1690273870637629)"
#       },


@dataclass
class WorkflowState:
    id: str
    name: str
    type: str


@dataclass
class Issue:
    id: str
    title: str
    description: str
    created_at: str
    url: str
    state: WorkflowState


@dataclass
class User:
    id: str
    name: str
    email: str
    assigned_issues: list[Issue]


@dataclass
class Team:
    id: str
    name: str


def get_issue(id: str) -> Issue:
    query = """
    query Issue {
      issue(id: "%s") {
        id
        title
        description
        url
      }
    }
    """ % (
        id
    )
    data = gql_request(query)
    return Issue(**data["data"]["issue"])


class LinearClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def gql_request(self, query: str) -> dict:
        response = requests.post(
            LINEAR_URL,
            headers={"Authorization": self.api_key},
            json={"query": query},
        )

        return response.json()

    def get_me(self) -> User:
        query = """
        query Me {
          viewer {
            id
            name
            email
            assignedIssues {
                nodes {
                    id
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
        data = self.gql_request(query)
        viewer = data["data"]["viewer"]
        user = User(
            id=viewer["id"],
            name=viewer["name"],
            email=viewer["email"],
            assigned_issues=[
                Issue(
                    id=issue["id"],
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
                for issue in viewer["assignedIssues"]["nodes"]
            ],
        )
        return user

    def get_issue(self, id: str) -> Issue:
        query = """
        query Issue {
          issue(id: "%s") {
            id
            title
            description
          }
        }
        """ % (
            id
        )
        data = self.gql_request(query)
        return Issue(**data["data"]["issue"])

    def get_teams(self):
        query = """
        query Teams {
          teams {
            nodes {
              id
              name
            }
          }
        }
        """
        data = self.gql_request(query)
        return [Team(**team) for team in data["data"]["teams"]["nodes"]]


def main():
    client = LinearClient(LINEAR_API_KEY)
    me = client.get_me()
    print(f"Hello {me.name}! Your email is {me.email}")

    issue = client.get_issue("TRA-383")
    print(f"Found issue {issue.title} with description {issue.description}")

    teams = client.get_teams()
    print(f"Found {len(teams)} teams")


if __name__ == "__main__":
    main()
