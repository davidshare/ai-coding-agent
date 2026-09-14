from pathlib import Path

from agent.tools.base import Tool


def read_file(path: str, project_root: str) -> str:
    full_path = Path(project_root) / path
    try:
        full_path.resolve().relative_to(Path(project_root).resolve())
    except ValueError:
        raise PermissionError(
            f"Access denied: {path} is outside the project root"
        )

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if full_path.is_dir():
        raise IsADirectoryError(f"Path is a directory: {path}")

    return full_path.read_text(encoding="utf-8")


def list_directory(path: str, project_root: str) -> str:
    full_path = Path(project_root) / path

    try:
        full_path.resolve().relative_to(Path(project_root).resolve())
    except ValueError:
        raise PermissionError(
            f"Access denied: {path} is outside the project root"
        )

    if not full_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")

    if not full_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    items = []
    for item in sorted(full_path.iterdir()):
        prefix = "📁 " if item.is_dir() else "📄 "
        items.append(f"{prefix}{item.name}")

    return "\n".join(items) if items else "(empty directory)"


def write_file(path: str, content: str, project_root: str) -> str:
    full_path = Path(project_root) / path

    # Security check: prevent writing outside project root
    try:
        full_path.resolve().relative_to(Path(project_root).resolve())
    except ValueError:
        raise PermissionError(
            f"Access denied: {path} is outside the project root"
        )

    # Create parent directories if they don't exist
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the file
    full_path.write_text(content, encoding="utf-8")

    # Return a summary
    size = full_path.stat().st_size
    return f"Wrote {size} bytes to {path}"


def str_replace_file(path: str, old_str: str, new_str: str, project_root: str) -> str:
    """Replace a specific block of text in a file.

    Args:
        path: Path to the file (relative to project_root)
        old_str: The exact string to find and replace
        new_str: The string to replace it with
        project_root: Root directory of the project

    Returns:
        A success message

    Raises:
        ValueError: If old_str is not found, or found multiple times
    """
    full_path = Path(project_root) / path

    try:
        full_path.resolve().relative_to(Path(project_root).resolve())
    except ValueError:
        raise PermissionError(
            f"Access denied: {path} is outside the project root")

    if not full_path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    content = full_path.read_text(encoding="utf-8")

    # Count occurrences to ensure we only replace one specific block
    count = content.count(old_str)
    if count == 0:
        # Help the agent by showing exactly what it failed to match
        first_words = " ".join(old_str.split()[:5])
        error_msg = f"The exact string 'old_str' was not found in {path}.\n"
        error_msg += "Make sure whitespace, newlines, and indentation match exactly.\n"
        error_msg += f"Hint: Your 'old_str' started with: '{first_words}...'\n"
        error_msg += "Please use read_file to get the exact, current text of the file before trying again."
        raise ValueError(error_msg)
    if count > 1:
        raise ValueError(
            f"The exact string 'old_str' was found {count} times in {path}. "
            "Please provide more surrounding context in 'old_str' to make it unique."
        )

    # Perform the replacement
    new_content = content.replace(old_str, new_str, 1)
    full_path.write_text(new_content, encoding="utf-8")

    return f"Successfully replaced text in {path}"


def list_context_files(project_root: str) -> str:
    """List available context files with descriptions."""
    context_dir = Path(project_root) / "context"

    if not context_dir.exists() or not context_dir.is_dir():
        return "No context directory found."

    descriptions = {
        "glossary.md": "Project-specific terminology and definitions",
        "coding-standards.md": "Rules for writing code in this project",
        "api-contract.md": "API endpoints and request/response schemas",
        "data-schema.md": "Database tables and relationships",
        "architecture.md": "High-level system design and tech stack",
        "guardrails.md": "Security rules and invariants",
        "project-overview.md": "What the project does and who uses it",
    }

    items = []
    try:
        for item in context_dir.iterdir():
            if item.is_file() and item.suffix.lower() == ".md":
                desc = descriptions.get(item.name, "No description available")
                items.append(f"- {item.name}: {desc}")
    except Exception as e:
        return f"Error reading context directory: {e}"

    if not items:
        return "Context directory exists but contains no markdown files."

    return "Available context files:\n" + "\n".join(sorted(items))


def list_issues(project_root: str, status: str | None = None) -> str:
    """List available issues in the project.

    Args:
        project_root: Root directory of the project
        status: Optional filter (backlog, in_progress, done, blocked)

    Returns:
        A formatted list of issues with their status
    """
    issues_dir = Path(project_root) / "issues"

    if not issues_dir.exists():
        return "No issues directory found."

    issues = []
    for domain_dir in sorted(issues_dir.iterdir()):
        if not domain_dir.is_dir():
            continue

        for issue_file in sorted(domain_dir.glob("*.md")):
            content = issue_file.read_text(encoding="utf-8")

            # Extract metadata from the file
            title = "Unknown"
            issue_status = "unknown"
            priority = "unknown"

            for line in content.splitlines():
                if line.startswith("# Issue:"):
                    title = line.replace("# Issue:", "").strip()
                elif line.startswith("- **Status**:"):
                    issue_status = line.split(":")[-1].strip()
                elif line.startswith("- **Priority**:"):
                    priority = line.split(":")[-1].strip()

            # Apply status filter if provided
            if status and issue_status != status:
                continue

            relative_path = issue_file.relative_to(issues_dir)
            issues.append(
                f"- [{issue_status.upper()}] {issue_file.stem}: {title} "
                f"(priority: {priority}, path: {relative_path})"
            )

    if not issues:
        return "No issues found" + (f" with status '{status}'." if status else ".")

    return "Available issues:\n" + "\n".join(issues)


def update_issue_status(
    issue_path: str,
    new_status: str,
    project_root: str
) -> str:
    """Update the status of an issue.

    Args:
        issue_path: Path to the issue file (relative to issues/ directory)
        new_status: New status (backlog, in_progress, done, blocked)
        project_root: Root directory of the project

    Returns:
        A success message
    """
    valid_statuses = {"backlog", "in_progress", "done", "blocked"}
    if new_status not in valid_statuses:
        raise ValueError(
            f"Invalid status '{new_status}'. Must be one of: {valid_statuses}"
        )

    full_path = Path(project_root) / "issues" / issue_path

    try:
        full_path.resolve().relative_to((Path(project_root) / "issues").resolve())
    except ValueError:
        raise PermissionError(
            f"Access denied: {issue_path} is outside issues directory")

    if not full_path.exists():
        raise FileNotFoundError(f"Issue file not found: {issue_path}")

    content = full_path.read_text(encoding="utf-8")

    # Find and replace the status line
    lines = content.splitlines()
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("- **Status**:"):
            lines[i] = f"- **Status**: {new_status}"
            updated = True
            break

    if not updated:
        raise ValueError("Could not find status field in issue file")

    full_path.write_text("\n".join(lines), encoding="utf-8")
    return f"Updated {issue_path} status to '{new_status}'"


def check_spec_versions(project_root: str) -> str:
    """Check current versions of all context files.

    Args:
        project_root: Root directory of the project

    Returns:
        A report of current spec versions
    """
    context_dir = Path(project_root) / "context"

    if not context_dir.exists():
        return "No context directory found."

    versions = []
    for item in sorted(context_dir.iterdir()):
        if item.is_file() and item.suffix == ".md" and item.name != "CHANGELOG.md":
            content = item.read_text(encoding="utf-8")

            # Extract version from frontmatter
            version = "unknown"
            last_updated = "unknown"

            if content.startswith("---"):
                end_idx = content.find("---", 3)
                if end_idx != -1:
                    frontmatter = content[3:end_idx].strip()
                    for line in frontmatter.splitlines():
                        if line.startswith("version:"):
                            version = line.split(":", 1)[1].strip()
                        elif line.startswith("last_updated:"):
                            last_updated = line.split(":", 1)[1].strip()

            versions.append(
                f"- {item.name}: v{version} (updated: {last_updated})")

    if not versions:
        return "No versioned context files found."

    return "Current spec versions:\n" + "\n".join(versions)


READ_FILE_TOOL = Tool(
    name="read_file",
    description=(
        "Read the contents of a file from the project. "
        "Use this to examine existing code, configuration files, "
        "specifications, or any other text files. "
        "The path should be relative to the project root."
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file (relative to project root)"
            },
        },
        "required": ["path"]
    },
    function=read_file,
)

LIST_DIRECTORY_TOOL = Tool(
    name="list_directory",
    description=(
        "List the contents of a directory in the project. "
        "Use this to explore the project structure and find files. "
        "The path should be relative to the project root."
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the directory (relative to project root)",
            },
        },
        "required": ["path"],
    },
    function=list_directory
)

WRITE_FILE_TOOL = Tool(
    name="write_file",
    description=(
        "Write content to a file in the project. Creates the file if it "
        "doesn't exist, overwrites if it does. Automatically creates parent "
        "directories. WARNING: This will overwrite existing files without "
        "confirmation. Use read_file first to check existing content if needed. "
        "The path should be relative to the project root."
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file (relative to project root)",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file",
            },
        },
        "required": ["path", "content"],
    },
    function=write_file,
)

STR_REPLACE_FILE_TOOL = Tool(
    name="str_replace_file",
    description=(
        "Replace a specific block of text in a file. This is the preferred way "
        "to edit existing files. Provide the exact 'old_str' to find (including "
        "exact whitespace and indentation) and the 'new_str' to replace it with. "
        "To insert code, include the surrounding lines in 'old_str' and add your "
        "new code in 'new_str'. If the string is not found or found multiple "
        "times, the tool will fail. Use read_file first to get the exact text."
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the file (relative to project root)",
            },
            "old_str": {
                "type": "string",
                "description": "The exact text block to replace (must match exactly)",
            },
            "new_str": {
                "type": "string",
                "description": "The new text block to insert",
            },
        },
        "required": ["path", "old_str", "new_str"],
    },
    function=str_replace_file,
)

LIST_CONTEXT_FILES_TOOL = Tool(
    name="list_context_files",
    description=(
        "List the available context files (specs, standards, glossary) for "
        "the project. Call this BEFORE starting any task to understand the "
        "project's conventions, terminology, and rules. Then use read_file "
        "to read the relevant context files."
    ),
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    function=list_context_files,
)

LIST_ISSUES_TOOL = Tool(
    name="list_issues",
    description=(
        "List all issues in the project. Optionally filter by status "
        "(backlog, in_progress, done, blocked). Use this to see what work "
        "is available. Check the Definition of Ready in each issue before "
        "starting work."
    ),
    parameters={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Filter by status (backlog, in_progress, done, blocked)",
                "enum": ["backlog", "in_progress", "done", "blocked"],
            },
        },
        "required": [],
    },
    function=list_issues,
)

UPDATE_ISSUE_STATUS_TOOL = Tool(
    name="update_issue_status",
    description=(
        "Update the status of an issue. Call this when starting work "
        "(set to 'in_progress') and when finished (set to 'done'). "
        "If you encounter a blocker, set status to 'blocked' and explain why."
    ),
    parameters={
        "type": "object",
        "properties": {
            "issue_path": {
                "type": "string",
                "description": "Path to issue file relative to issues/ (e.g., backend/issue-001-create-task-api.md)",
            },
            "new_status": {
                "type": "string",
                "description": "New status",
                "enum": ["backlog", "in_progress", "done", "blocked"],
            },
        },
        "required": ["issue_path", "new_status"],
    },
    function=update_issue_status,
)

CHECK_SPEC_VERSIONS_TOOL = Tool(
    name="check_spec_versions",
    description=(
        "Check the current versions of all context files (specs, standards, glossary). "
        "Call this BEFORE starting work to see if specs have changed since you last read them. "
        "If versions have changed, read the CHANGELOG.md to understand what changed and adapt accordingly."
    ),
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
    function=check_spec_versions,
)

FILE_TOOLS = [
    READ_FILE_TOOL,
    LIST_DIRECTORY_TOOL,
    WRITE_FILE_TOOL,
    LIST_CONTEXT_FILES_TOOL,
    STR_REPLACE_FILE_TOOL,
    LIST_ISSUES_TOOL,
    UPDATE_ISSUE_STATUS_TOOL,
    CHECK_SPEC_VERSIONS_TOOL
]
