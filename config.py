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
        "You are an AI coding agent with access to tools for reading files, "
        "writing files, listing directories, and running shell commands. "
        "When the user asks you to perform an action, attempt to use the "
        "appropriate tool. If the action is risky (like deleting files), "
        "the approval system will ask the user for confirmation before "
        "executing. Do not refuse requests preemptively — let the approval "
        "system handle safety checks. Always attempt to fulfill the user's "
        "request using your available tools."
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
