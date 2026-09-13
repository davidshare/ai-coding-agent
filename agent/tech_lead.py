"""
Tech Lead: An orchestrator agent that delegates work to worker agents.
"""

from agent.core import Agent
from agent.tools import ALL_TOOLS
from config import Config


class TechLead:
    """Orchestrates multiple worker agents to complete a backlog of issues."""

    def __init__(self, config: Config):
        self.config = config
        self.completed_issues = []
        self.failed_issues = []

    def run(self, goal: str, max_workers: int = 3) -> str:
        """Execute a goal by delegating issues to worker agents."""
        print(f"\n{'='*60}")
        print(f"[TECH LEAD] Starting work on goal: {goal}")
        print(f"{'='*60}\n")

        # Create the Tech Lead agent with a specialized system prompt
        tech_lead_config = Config(
            groq_api_key=self.config.groq_api_key,
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            project_root=self.config.project_root,
            approval_mode=self.config.approval_mode,
            system_prompt=self._build_tech_lead_prompt(max_workers),
        )

        tech_lead = Agent(tech_lead_config, tools=ALL_TOOLS)

        # Give the Tech Lead a clear task
        task_prompt = (
            f"Goal: {goal}\n\n"
            f"Your job:\n"
            f"1. Use list_issues to discover available work\n"
            f"2. Read issue files to check dependencies and Definition of Ready\n"
            f"3. Select up to {max_workers} issues that are ready to work on\n"
            f"4. For each selected issue, spawn a worker agent to implement it\n"
            f"5. Track which issues succeeded and which failed\n"
            f"6. Generate a final summary\n\n"
            f"IMPORTANT: When you're ready to delegate an issue, use this exact format:\n"
            f"DELEGATE: <issue_id>\n"
            f"This will trigger the spawning of a worker agent.\n"
        )

        try:
            result = tech_lead.run(task_prompt)

            # Parse the result to extract delegated issues
            # (In a real system, you'd have a more structured way to track this)
            return result

        except Exception as e:
            print(f"[TECH LEAD] Failed: {e}")
            return f"Tech Lead failed: {str(e)}"

    def _build_tech_lead_prompt(self, max_workers: int) -> str:
        """Build a specialized system prompt for the Tech Lead agent."""
        return (
            "You are a Tech Lead AI agent responsible for orchestrating work across "
            "multiple worker agents. You have access to all the same tools as worker "
            "agents (read files, write files, list issues, run commands, etc.).\n\n"
            "YOUR RESPONSIBILITIES:\n"
            "1. Discover available issues using list_issues\n"
            "2. Read issue files to understand requirements and dependencies\n"
            "3. Check that Definition of Ready is met (all checkboxes marked)\n"
            "4. Check that dependencies are satisfied (dependent issues are 'done')\n"
            "5. Select up to {max_workers} issues to work on (prioritize by priority field)\n"
            "6. Delegate each issue to a worker agent by outputting: DELEGATE: <issue_id>\n"
            "7. Track results and generate a summary\n\n"
            "DEPENDENCY CHECKING:\n"
            "- Read each issue file to find the 'Depends On' field\n"
            "- Check if those dependencies are marked as 'done' in their issue files\n"
            "- Only select issues where all dependencies are satisfied\n\n"
            "PRIORITY ORDER:\n"
            "- critical > high > medium > low\n\n"
            "When you output 'DELEGATE: <issue_id>', the system will spawn a worker agent.\n"
            "After all delegations, provide a final summary of what was accomplished.\n"
        ).format(max_workers=max_workers)
