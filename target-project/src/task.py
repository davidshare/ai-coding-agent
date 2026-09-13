"""Task domain model.

Defines the :class:`Task` dataclass and the :class:`TaskStatus` enum that
represent a unit of work that can be claimed by an AI agent.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    """Lifecycle states a task can be in."""

    BACKLOG = "backlog"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class TaskError(Exception):
    """Base exception for task-related errors."""


class InvalidStateTransitionError(TaskError):
    """Raised when an illegal status transition is attempted."""


@dataclass
class Task:
    """A unit of work that can be claimed by an AI agent.

    Args:
        title: Short human-readable name for the task.
        description: Longer explanation of what the task involves.
        id: Unique identifier. Generated automatically if omitted.
        status: Current lifecycle state. Defaults to :attr:`TaskStatus.BACKLOG`.
        owner: Agent ID of the current owner, or ``None`` if unclaimed.

    Raises:
        InvalidStateTransitionError: If a status transition is attempted
            that is not allowed by the lifecycle rules.
    """

    title: str
    description: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: TaskStatus = TaskStatus.BACKLOG
    owner: str | None = None

    def claim(self, agent_id: str) -> None:
        """Claim the task for the given agent.

        Only one agent can claim a task at a time, and a task can only be
        claimed while it is in the backlog.

        Args:
            agent_id: The ID of the agent claiming the task.

        Raises:
            InvalidStateTransitionError: If the task is not in the backlog.
        """
        if self.status is not TaskStatus.BACKLOG:
            raise InvalidStateTransitionError(
                f"Cannot claim task {self.id} in status {self.status.value}"
            )
        self.status = TaskStatus.CLAIMED
        self.owner = agent_id

    def start(self) -> None:
        """Move the task from claimed to in progress.

        Raises:
            InvalidStateTransitionError: If the task is not claimed.
        """
        if self.status is not TaskStatus.CLAIMED:
            raise InvalidStateTransitionError(
                f"Cannot start task {self.id} in status {self.status.value}"
            )
        self.status = TaskStatus.IN_PROGRESS

    def submit_for_review(self) -> None:
        """Move the task from in progress to review.

        Raises:
            InvalidStateTransitionError: If the task is not in progress.
        """
        if self.status is not TaskStatus.IN_PROGRESS:
            raise InvalidStateTransitionError(
                f"Cannot submit task {self.id} for review in status "
                f"{self.status.value}"
            )
        self.status = TaskStatus.REVIEW

    def complete(self) -> None:
        """Move the task from review to done.

        Raises:
            InvalidStateTransitionError: If the task is not in review.
        """
        if self.status is not TaskStatus.REVIEW:
            raise InvalidStateTransitionError(
                f"Cannot complete task {self.id} in status {self.status.value}"
            )
        self.status = TaskStatus.DONE
        self.owner = None

    def __str__(self) -> str:
        """Return a human-readable representation of the task."""
        owner = self.owner or "unassigned"
        return f"Task({self.id}, {self.title!r}, {self.status.value}, {owner})"


def claim_task(task: Task, agent_id: str) -> Task:
    """Claim a task for an agent.

    Convenience wrapper around :meth:`Task.claim` that returns the task,
    allowing callers to chain the call.

    Args:
        task: The task to claim.
        agent_id: The ID of the agent claiming the task.

    Returns:
        The same task, now claimed by the given agent.

    Raises:
        InvalidStateTransitionError: If the task is not in the backlog.
    """
    task.claim(agent_id)
    return task