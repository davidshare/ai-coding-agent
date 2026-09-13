from src.task import Task, TaskStatus, InvalidStateTransitionError

t = Task(title="Fix bug", description="Fix the bug")
assert t.status is TaskStatus.BACKLOG
t.claim("agent-1")
assert t.status is TaskStatus.CLAIMED and t.owner == "agent-1"
t.start()
t.submit_for_review()
t.complete()
assert t.status is TaskStatus.DONE and t.owner is None
try:
    t.claim("agent-2")
except InvalidStateTransitionError:
    pass
else:
    raise SystemExit("expected error")
print("OK", t)