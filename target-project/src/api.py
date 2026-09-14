"""FastAPI application for the task management service.

Exposes HTTP endpoints for creating and managing :class:`Task` objects.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.task import Task


class TaskCreateRequest(BaseModel):
    """Request body for creating a task.

    Args:
        title: Short human-readable name for the task. Required.
        description: Longer explanation of what the task involves.
    """

    title: str = Field(..., min_length=1)
    description: str = ""


class TaskResponse(BaseModel):
    """Response body representing a created task.

    Args:
        id: Unique identifier of the task.
        title: Short human-readable name for the task.
        description: Longer explanation of what the task involves.
        status: Current lifecycle state.
        owner: Agent ID of the current owner, or ``None`` if unclaimed.
    """

    id: str
    title: str
    description: str
    status: str
    owner: str | None


app = FastAPI(title="Task Management Service")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a 400 response for request validation errors.

    Args:
        request: The incoming HTTP request.
        exc: The validation error raised by Pydantic.

    Returns:
        A JSON response with status 400 and the validation details.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors()},
    )


@app.post(
    "/api/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(request: TaskCreateRequest) -> TaskResponse:
    """Create a new task.

    Args:
        request: The task creation request containing title and description.

    Returns:
        The created task serialized as a :class:`TaskResponse`.
    """
    task = Task(title=request.title, description=request.description)
    return TaskResponse(
        id=str(task.id),
        title=task.title,
        description=task.description,
        status=task.status.value,
        owner=task.owner,
    )