import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    provider: str = os.getenv("LLM_PROVIDER", "groq").lower()
    api_key: str = os.getenv("API_KEY", "")
    model: str = os.getenv("LLM_MODEL", "qwen/qwen3.8-27b")
    max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    project_root: Path = Path(os.getenv("PROJECT_ROOT", "./target-project"))
    # auto | confirm_writes | confirm_commands | confirm_all | smart
    approval_mode: str = os.getenv("APPROVAL_MODE", "smart")
    system_prompt: str = field(init=False)
    max_history_length: int = int(os.getenv("MAX_HISTORY_LENGTH", "10"))

    def __post_init__(self):
        if not self.api_key:
            raise ValueError("API_KEY environment variable not send in .env")
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load the system prompt from the prompts/ directory"""

        prompt_dir = Path(__file__).parent.parent / "prompts"
        main_prompt = prompt_dir / "system.md"

        if main_prompt.exists():
            return main_prompt.read_text(encoding="utf-8")

        return "You are an AI coding. Agent follow instructions carefully."

    @classmethod
    def from_env(cls) -> 'Config':
        return cls()
