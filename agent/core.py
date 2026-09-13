import json

from agent.approval import ApprovalManager
from agent.llm import LLMclient
from agent.tools.base import Tool
from config import Config


class Agent:
    def __init__(self, config: Config, tools: list[Tool]):
        self.llm = LLMclient(config)
        self.tools = {tool.name: tool for tool in tools}
        self.history: list[dict] = []
        self.project_root = str(config.project_root)
        self.approval = ApprovalManager(config.approval_mode)
        self.system_prompt = config.system_prompt

    def run(self, user_message: str) -> str:

        if not self.history and self.system_prompt:
            self.history.append({
                "role": "system",
                "content": self.system_prompt,
            })

        self.history.append({
            "role": "user",
            "content": user_message,
        })

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            print(f"\n[Iteration {iteration}]")

            tool_schemas = [tool.to_json_schema()
                            for tool in self.tools.values()]
            response = self.llm.complete(
                messages=self.history,
                tools=tool_schemas if tool_schemas else None,
            )

            self.history.append(response)

            if "tool_calls" in response and response["tool_calls"]:
                for tool_call in response["tool_calls"]:
                    self._execute_tool_call(tool_call)
            else:
                return response["content"]
        raise RuntimeError(
            f"Agent exceeded maximum iterations ({max_iterations}). "
            "This usually means the agent is stuck in a loop."
        )

    def _execute_tool_call(self, tool_call: dict) -> None:
        function_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])

        print(f"Calling tool: {function_name}({arguments})")

        if function_name not in self.tools:
            result = f"Error: Tool '{function_name}' not found"
        else:
            try:
                tool = self.tools[function_name]

                # Check approval before execution
                approved = True
                if function_name == "write_file":
                    if self.approval.needs_approval_for_write(
                        arguments["path"], arguments["content"], self.project_root
                    ):
                        approved = self.approval.request_write_approval(
                            arguments["path"], arguments["content"], self.project_root
                        )
                elif function_name == "run_command":
                    if self.approval.needs_approval_for_command(arguments["command"]):
                        approved = self.approval.request_command_approval(
                            arguments["command"], self.project_root
                        )

                if not approved:
                    result = "User denied this action. Please try a different approach."
                    print(f"  [DENIED] User rejected the action")
                else:
                    arguments["project_root"] = self.project_root
                    result = tool.execute(**arguments)
                    print(f"  [OK] Result: {str(result)[:200]}...")

                print(f"Tool result:\n{str(result)[:200]}...")
            except Exception as e:
                result = f"Error executing tool: {str(e)}"
                print(f"Tool error: {result}")
        self.history.append({
            "role": "tool",
            "tool_call_id": tool_call['id'],
            "content": str(result),
        })

    def reset(self) -> None:
        self.history = []
