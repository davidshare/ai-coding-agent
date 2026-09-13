import traceback

from agent.core import Agent
from agent.tools import ALL_TOOLS
from config import Config


def main():
    print("AI Coding Agent")
    print("=" * 50)

    try:
        config = Config.from_env()
    except ValueError as e:
        print(f"configuration error: {e}")
        return

    agent = Agent(config, tools=ALL_TOOLS)
    print(f"Agent initialised with {len(ALL_TOOLS)} tools")
    print(f" Project root: {config.project_root}")
    print(f"Model: {config.model}")
    print("\nType your message: (or 'quit' to exit)")
    print("=" * 50)

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
                print("Conversation reset")
                continue

            response = agent.run(user_input)
            print(f"\n Agent: {response}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print(f"Full error details:")
            traceback.print_exc()


if __name__ == "__main__":
    main()
