import shlex
import subprocess
from pathlib import Path

from agent.tools.base import Tool

BLOCKED_PATTERNS = [
    ":(){:|:&};:",
    "mkfs.",
    "dd if=/dev/zero",
]


def _validate_command_paths(command: str, project_root: str) -> None:
    """Validate that all paths in the command are within project_root."""
    root_path = Path(project_root).resolve()
    parts = shlex.split(command)

    for part in parts:
        if part.startswith("-"):
            continue

        if ".." in part:
            try:
                resolved = (root_path / part).resolve()
                resolved.relative_to(root_path)
            except ValueError:
                raise ValueError(f"Path escapes project root: {part}")

        if part.startswith("/"):
            try:
                Path(part).resolve().relative_to(root_path)
            except ValueError:
                raise ValueError(f"Absolute path outside project root: {part}")


def run_command(
    command: str,
    project_root: str,
    timeout: int = 30,
    max_output: int = 10000,
) -> str:
    root_path = Path(project_root).resolve()
    if not root_path.is_dir():
        raise ValueError(f"Project root does not exist: {project_root}")

    command_lower = command.lower().strip()
    for pattern in BLOCKED_PATTERNS:
        if pattern in command_lower:
            raise ValueError(f"Blocked command pattern: {pattern}")
    
    _validate_command_paths(command, project_root)

    try:
        args = shlex.split(command)
    except ValueError as e:
        raise ValueError(f"Invalid command syntax: {e}")

    result = subprocess.run(
        args,
        cwd=root_path,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    stdout = result.stdout[:max_output]
    stderr = result.stderr[:max_output]

    truncated_note = ""
    if len(result.stdout) > max_output:
        truncated_note += f"\n[stdout truncated: {len(result.stdout)} bytes total]"
    if len(result.stderr) > max_output:
        truncated_note += f"\n[stderr truncated: {len(result.stderr)} bytes total]"

    output_parts = []
    if stdout:
        output_parts.append(f"STDOUT:\n{stdout}")
    if stderr:
        output_parts.append(f"STDERR:\n{stderr}")
    output_parts.append(f"Exit code: {result.returncode}")

    return "\n".join(output_parts) + truncated_note


RUN_COMMAND_TOOL = Tool(
    name="run_command",
    description=(
        "Execute a shell command in the project directory. Use this to run "
        "tests (pytest, npm test), install dependencies (pip install, npm install), "
        "check syntax (python -m py_compile), lint code, or perform other "
        "operations. The command runs in the project root. Output is capped at "
        "10KB. Use short, focused commands. Avoid interactive commands. "
        "Commands are blocked if they include destructive operations like "
        "'rm -rf /'. Always check exit code: 0 means success, non-zero means error."
    ),
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute",
            },
            "timeout": {
                "type": "integer",
                "description": "Maximum seconds to wait (default 30)",
            },
        },
        "required": ["command"],
    },
    function=run_command,
)


COMMAND_TOOLS = [RUN_COMMAND_TOOL]
