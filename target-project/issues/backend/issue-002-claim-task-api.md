# Issue: Claim Task API Endpoint

## Metadata
- **ID**: issue-002
- **Domain**: backend
- **Status**: in_progress
- **Priority**: high

## Definition of Ready
- [x] Task model exists
- [x] issue-001 is complete

## Description
Create an endpoint that allows an agent to claim a task.

## Acceptance Criteria
- [ ] Endpoint: POST /api/tasks/{task_id}/claim
- [ ] Request body: {"agent_id": str}
- [ ] Returns: 200 with claimed task
- [ ] Returns: 409 if task already claimed
- [ ] Returns: 404 if task not found
- [ ] Uses Task.claim() method

## Dependencies
- **Depends On**: issue-001
- **Blocks**: (none)

## Notes
Use the existing Task.claim() method. Handle InvalidStateTransitionError.