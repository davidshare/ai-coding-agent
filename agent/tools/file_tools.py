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

FILE_TOOLS = [READ_FILE_TOOL, LIST_DIRECTORY_TOOL,
              WRITE_FILE_TOOL, LIST_CONTEXT_FILES_TOOL]
