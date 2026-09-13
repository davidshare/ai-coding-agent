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

    @classmethod
    def from_env(cls) -> 'Config':
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set. "
                "Please set it with: export GROQ_API_KEY='your-key-here'"
            )
        return cls(groq_api_key=api_key)
