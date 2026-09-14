import sys
from pathlib import Path

from agent.core import Agent
from agent.tools import ALL_TOOLS
from config import Config


def main():
    print("AI Coding Agent")
    print("=" * 50)

    try:
        config = Config.from_env()
    except ValueError as e:
        print(f"Configuration error: {e}")
        return

    agent = Agent(config, tools=ALL_TOOLS)
    print(f"Agent initialised with {len(ALL_TOOLS)} tools")
    print(f"Provider: {config.provider}")
    print(f"Model: {config.model}")
    print(f"Project root: {config.project_root}")
    print("\nType your message: (or 'quit' to exit)")
    print("=" * 50)

    # Handle Tech Lead mode
    if len(sys.argv) > 1 and sys.argv[1] == "--tech-lead":
        from agent.tech_lead import TechLead

        goal = " ".join(sys.argv[2:]) if len(
            sys.argv) > 2 else "Work through the issue backlog"

        tech_lead = TechLead(config)
        summary = tech_lead.run(goal, max_workers=3)
        print(summary)
        return

    has_state = agent.load_state()

    # Standard interactive mode
    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if user_input.lower() == "reset":
                agent.reset()
                state_file = Path(config.project_root) / ".agent_state.json"
                if state_file.exists():
                    state_file.unlink()

                print("Conversation reset and state cleared")
                continue

            if user_input.lower() == "resume":
                if has_state and len(agent.history) > 0:
                    print("Resuming previous session...")
                    # The agent will automatically process the last tool call or continue
                    # We just need to trigger the loop. We can do this by re-running the last assistant turn.
                    # For simplicity, we just let the user provide the next prompt, but the history is intact.
                    print("History restored. Please provide the next instruction.")
                    continue
                else:
                    print("No previous state found to resume.")
                    continue

            response = agent.run(user_input)
            print(f"\nAgent: {response}")

        except KeyboardInterrupt:
            print("\n\n[AGENT] Saving state before shutdown...")
            agent.save_state()
            print("Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] {e}")
            # Save state even on crash
            agent.save_state()
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
