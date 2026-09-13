import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    groq_api_key: str
    model: str = "qwen/qwen3.8-27b"
    max_tokens: int = 4096
    temperature: float = 0.3
    project_root: Path = Path('./target-project')

    # auto | confirm_writes | confirm_commands | confirm_all | smart
    approval_mode: str = "smart"
    system_prompt: str = (
        "You are an AI coding agent working on a specific project. "
        "You have access to tools for reading files, writing files, "
        "listing directories, running shell commands, and listing "
        "context files (specs, standards, glossary).\n\n"
        "BEFORE starting any task:\n"
        "1. Call list_context_files to see what project context is available\n"
        "2. Read the relevant context files using read_file (especially "
        "glossary.md and coding-standards.md)\n"
        "3. Follow the rules and terminology defined in those files\n\n"
        "When writing code:\n"
        "- Use the exact terminology from the glossary\n"
        "- Follow the coding standards strictly\n"
        "- Match the project's existing patterns\n\n"
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
