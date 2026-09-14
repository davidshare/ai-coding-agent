import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any


class ObservabilityManager:
    """Tracks agent execution metrics and writes them to a local JSONL log."""

    def __init__(self, project_root: str):
        self.log_dir = Path(project_root) / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"run_{self.run_id}.jsonl"
        self.start_time = time.time()
        self.iteration_count = 0
        self.total_tokens = 0

        self.log_event("run_start", {})

    def log_event(self, event_type: str, data: dict[str, Any]):
        """Write a single event to the JSONL log file."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "run_id": self.run_id,
            "event_type": event_type,
            "data": data
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def track_iteration(self):
        self.iteration_count += 1

    def track_llm_response(self, response: dict):
        """Track token usage from LLM responses."""
        usage = response.get("usage", {})
        tokens = usage.get("total_tokens", 0)
        self.total_tokens += tokens

        self.log_event("llm_response", {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": tokens,
            "tool_calls": len(response.get("tool_calls", [])),
        })

    def track_tool_execution(self, tool_name: str, arguments: dict, success: bool, latency: float, error: str | None = None):
        """Track tool execution metrics."""
        self.log_event("tool_call", {
            "tool_name": tool_name,
            "arguments": arguments,
            "success": success,
            "latency_seconds": round(latency, 3),
            "error": error,
        })

    def finalize_run(self, success: bool, final_message: str):
        """Write the final summary of the run."""
        total_time = time.time() - self.start_time
        self.log_event("run_end", {
            "success": success,
            "total_time_seconds": round(total_time, 2),
            "total_iterations": self.iteration_count,
            "total_tokens_used": self.total_tokens,
            # Truncate to prevent massive log files
            "final_message": final_message[:500],
        })
        print(f"\n[OBSERVABILITY] Run logged to: {self.log_file}")
        print(
            f"[OBSERVABILITY] Stats: {self.iteration_count} iterations, {self.total_tokens} tokens, {total_time:.2f}s")
