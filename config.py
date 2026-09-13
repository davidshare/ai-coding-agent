import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    groq_api_key: str
    model: str = "qwen/qwen3.8-27b"
    # max_tokens: int = 4096
    max_tokens: int = 2000
    temperature: float = 0.3
    project_root: Path = Path('./target-project')

    # auto | confirm_writes | confirm_commands | confirm_all | smart
    approval_mode: str = "smart"
    system_prompt: str = (
        "You are an AI coding agent working on a specific project. "
        "You have access to tools for reading files, writing files, "
        "listing directories, running shell commands, listing context "
        "files, editing files, listing issues, and updating issue status.\n\n"
        "BEFORE starting any task:\n"
        "1. Call list_context_files to see what project context is available\n"
        "2. Read the relevant context files (glossary.md, coding-standards.md)\n"
        "3. Follow the rules and terminology defined in those files\n\n"
        "WORKING ON ISSUES:\n"
        "When asked to work on issues or when you need to decide what to do:\n"
        "1. Call list_issues to see available work\n"
        "2. Pick an issue with status 'backlog' where all Definition of Ready "
        "items are checked\n"
        "3. Read the full issue file using read_file\n"
        "4. Update the issue status to 'in_progress' using update_issue_status\n"
        "5. Implement the work following the Acceptance Criteria\n"
        "6. Verify all acceptance criteria are met\n"
        "7. Update the issue status to 'done'\n\n"
        "If you cannot complete an issue (missing dependencies, unclear "
        "requirements), set status to 'blocked' and explain why.\n\n"
        "When writing code:\n"
        "- Use the exact terminology from the glossary\n"
        "- Follow the coding standards strictly\n"
        "- Match the project's existing patterns\n\n"
        "ENVIRONMENT SETUP:\n"
        "If this is your first time working on this project:\n"
        "1. Check if issue-000 (setup environment) exists and is in backlog\n"
        "2. If yes, work on that issue FIRST before any other issues\n"
        "3. Use uv for all package management\n"
        "4. Create and activate a virtual environment\n"
        "5. Install dependencies as you discover them\n"
        "6. Document the setup in SETUP.md\n\n"
        "FILE SIZE LIMITS:\n"
        "If you need to create or edit a file that will be longer than 40 lines:\n"
        "1. Do NOT write it all at once.\n"
        "2. Write the first 30-40 lines using write_file.\n"
        "3. Use str_replace_file to append the next 30-40 lines.\n"
        "4. Repeat until the file is complete.\n"
        "This prevents output truncation and token limit errors.\n\n"
        "When the user asks you to perform an action, attempt to use the "
        "appropriate tool. If the action is risky, the approval system will "
        "ask the user for confirmation. Do not refuse requests preemptively."
    )

    @classmethod
    def from_env(cls) -> 'Config':
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set. "
                "Please set it with: export GROQ_API_KEY='your-key-here'"
            )
        return cls(groq_api_key=api_key)
