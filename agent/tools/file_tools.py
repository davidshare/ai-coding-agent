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

FILE_TOOLS = [READ_FILE_TOOL, LIST_DIRECTORY_TOOL, WRITE_FILE_TOOL]
