# Issue: Create Task API Endpoint

## Metadata
- **ID**: issue-001
- **Domain**: backend
- **Status**: done
- **Priority**: high

## Definition of Ready
- [x] Task model exists (src/task.py)
- [x] Coding standards defined
- [x] Glossary defined

## Description
Create a FastAPI endpoint that accepts a task creation request and returns the created task.

## Acceptance Criteria
- [ ] Endpoint: POST /api/tasks
- [ ] Request body: {"title": str, "description": str}
- [ ] Returns: 201 with created task JSON
- [ ] Returns: 400 if title is missing
- [ ] Uses the Task class from src/task.py
- [ ] Follows coding standards (type hints, docstrings)

## Dependencies
- **Depends On**: (none)
- **Blocks**: issue-002

## Notes
Use FastAPI with Pydantic for request validation.