"""
Approval system for human-in-the-loop control.

Shows previews of actions and asks the user to approve or deny.
Supports different modes for different levels of automation.
"""

from pathlib import Path


class ApprovalManager:
    """Manages approval flow for agent actions.

    Attributes:
        mode: The approval mode (auto, confirm_writes, confirm_commands, confirm_all, smart)
    """

    def __init__(self, mode: str = "smart"):
        if mode not in ("auto", "confirm_writes", "confirm_commands", "confirm_all", "smart"):
            raise ValueError(f"Invalid approval mode: {mode}")
        self.mode = mode

    def needs_approval_for_write(self, path: str, content: str, project_root: str) -> bool:
        """Check if a write operation needs approval."""
        if self.mode == "auto":
            return False
        if self.mode in ("confirm_writes", "confirm_all"):
            return True
        if self.mode == "smart":
            # In smart mode, ask if file exists (overwrite) or is in a sensitive location
            full_path = Path(project_root) / path
            if full_path.exists():
                return True
            # Ask for config files, env files, etc.
            sensitive_names = {".env", "config.py", "settings.py", "secrets"}
            if full_path.name in sensitive_names:
                return True
            return False
        return False

    def needs_approval_for_command(self, command: str) -> bool:
        """Check if a command needs approval."""
        if self.mode == "auto":
            return False
        if self.mode in ("confirm_commands", "confirm_all"):
            return True
        if self.mode == "smart":
            # In smart mode, ask for potentially destructive commands
            risky_prefixes = (
                "rm ", "rm\t", "sudo ", "git push", "git reset",
                "git checkout", "git clean", "pip uninstall",
                "npm uninstall", "drop ", "delete ", "truncate ")
            cmd_lower = command.lower().strip()
            return any(
                cmd_lower.startswith(p) or f" {p}" in f" {cmd_lower}" for p in risky_prefixes
            )
        return False

    def request_write_approval(self, path: str, content: str, project_root: str) -> bool:
        """Show a write preview and ask for approval.

        Returns:
            True if approved, False if denied
        """
        full_path = Path(project_root) / path
        exists = full_path.exists()
        action = "OVERWRITE" if exists else "CREATE"

        print(f"\n{'='*60}")
        print(f"[APPROVAL REQUEST] {action} FILE")
        print(f"{'='*60}")
        print(f"Path: {path}")
        print(f"Size: {len(content)} bytes, {len(content.splitlines())} lines")

        if exists:
            old_size = full_path.stat().st_size
            print(f"Existing file: {old_size} bytes (will be replaced)")

        # Show content preview (first 10 and last 5 lines)
        lines = content.splitlines()
        print(f"\n--- Content Preview ---")
        if len(lines) <= 15:
            print(content)
        else:
            print("\n".join(lines[:10]))
            print(f"\n... ({len(lines) - 15} lines omitted) ...\n")
            print("\n".join(lines[-5:]))
        print(f"{'='*60}")

        return self._ask_approval()

    def request_command_approval(self, command: str, project_root: str) -> bool:
        """Show a command preview and ask for approval.

        Returns:
            True if approved, False if denied
        """
        print(f"\n{'='*60}")
        print(f"[APPROVAL REQUEST] RUN COMMAND")
        print(f"{'='*60}")
        print(f"Working directory: {project_root}")
        print(f"Command: {command}")
        print(f"{'='*60}")

        return self._ask_approval()

    def _ask_approval(self) -> bool:
        """Prompt the user for approval.

        Returns:
            True if approved, False if denied
        """
        while True:
            response = input(
                "\nApprove? [y]es / [n]o / [a]lways for this session: ").strip().lower()
            if response in ("y", "yes"):
                return True
            if response in ("n", "no"):
                return False
            if response in ("a", "always"):
                # Switch to auto mode for the rest of the session
                self.mode = "auto"
                print("[Switched to auto mode for this session]")
                return True
            print("Please enter y, n, or a")
