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


@dataclass
class User:
    id: str
    name: str
    email: str
    assigned_issues: list[Issue]
    """
    Issues assigned to the user.
    """
