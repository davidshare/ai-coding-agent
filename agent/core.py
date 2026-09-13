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

        max_iterations = 40
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

        try:
            arguments = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError as e:
            print(f"  [ERR] Invalid JSON from LLM: {e}")
            self.history.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": f"Error: The arguments provided were not valid JSON. Please ensure your tool call arguments are properly formatted JSON. Error details: {str(e)}",
            })
            return

        if function_name not in self.tools:
            result = f"Error: Tool '{function_name}' not found"
        else:
            try:
                tool = self.tools[function_name]

                # Check approval before execution
                approved = True
                if function_name in ("write_file", "append_to_file", "str_replace_file"):
                    if self.approval.needs_approval_for_write(
                        arguments.get("path", ""), arguments.get(
                            "content", ""), self.project_root
                    ):
                        approved = self.approval.request_write_approval(
                            arguments.get("path", ""), arguments.get(
                                "content", ""), self.project_root
                        )
                elif function_name == "run_command":
                    if self.approval.needs_approval_for_command(arguments.get("command", "")):
                        approved = self.approval.request_command_approval(
                            arguments.get("command", ""), self.project_root
                        )

                if not approved:
                    result = "User denied this action. Please try a different approach."
                    print(f"[DENIED] User rejected the action")
                else:
                    # RETRY LOGIC: Allow up to 3 attempts for transient or fixable errors
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            # Inject project_root into arguments
                            arguments["project_root"] = self.project_root

                            # Execute the tool
                            result = tool.execute(**arguments)
                            print(f"  [OK] Result: {str(result)[:200]}...")
                            break  # Success, exit the retry loop

                        except Exception as e:
                            error_msg = str(e)
                            print(
                                f"  [ERR] Attempt {attempt + 1}/{max_retries} failed: {error_msg[:100]}")

                            if attempt == max_retries - 1:
                                # Final attempt failed
                                result = f"Tool '{function_name}' failed after {max_retries} attempts. Last error: {error_msg}"
                            else:
                                # Feed the error back to the LLM so it can try to fix it
                                result = f"Error: {error_msg}. Please correct your arguments and try again."
                                # Add the error to history immediately so the LLM sees it on the next iteration
                                self.history.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "content": result,
                                })
                                # Return early to let the LLM process the error and generate a new tool call
                                return

            except Exception as e:
                result = f"Critical error executing tool: {str(e)}"
                print(f"  [CRITICAL] {result}")
        self.history.append({
            "role": "tool",
            "tool_call_id": tool_call['id'],
            "content": str(result),
        })

    def reset(self) -> None:
        self.history = []
