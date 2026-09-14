import json
import time

from agent.approval import ApprovalManager
from agent.llm import create_llm_client
from agent.observability import ObservabilityManager
from agent.tools.base import Tool
from config import Config


class Agent:
    def __init__(self, config: Config, tools: list[Tool]):
        self.llm = create_llm_client(config)
        self.tools = {tool.name: tool for tool in tools}
        self.history: list[dict] = []
        self.project_root = str(config.project_root)
        self.approval = ApprovalManager(config.approval_mode)
        self.system_prompt = config.system_prompt
        self.max_history_length = config.max_history_length
        self.obs = ObservabilityManager(self.project_root)

    def _trim_history(self) -> None:
        """Zero-cost history management. No LLM calls, no summarization."""
        if len(self.history) > self.max_history_length:
            print(
                f"  [MEMORY] Trimming history ({len(self.history)} msgs) to save tokens. Zero API cost.")

            system_msg = self.history[0]
            first_user_msg = next(
                (msg for msg in self.history if msg["role"] == "user"), None)

            recent_messages = self.history[-4:]

            self.history = [system_msg]
            if first_user_msg and first_user_msg not in recent_messages:
                self.history.append(first_user_msg)
            self.history.extend(recent_messages)

    def run(self, user_message: str) -> str:
        self.obs.log_event("user_prompt", {"message": user_message})

        final_output = ""
        success = False

        try:
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
                self.obs.track_iteration()

                if len(self.history) > self.max_history_length:
                    self._trim_history()

                print(
                    f"\n[Iteration {iteration}] (History length: {len(self.history)})")

                tool_schemas = [tool.to_json_schema()
                                for tool in self.tools.values()]
                response = self.llm.complete(
                    messages=self.history,
                    tools=tool_schemas if tool_schemas else None,
                )

                self.obs.track_llm_response(response)

                self.history.append(response)

                if "DELEGATE:" in response.get("content", ""):
                    import re
                    delegate_match = re.search(
                        r"DELEGATE:\s*(\S+)", response["content"])
                    if delegate_match:
                        issue_id = delegate_match.group(1)
                        print(
                            f"\n[AGENT] Detected DELEGATE command for {issue_id}")
                        self.history.append({
                            "role": "system",
                            "content": f"Worker agent spawned for {issue_id}. Continue with next issue or provide summary."
                        })
                        continue

                if "tool_calls" in response and response["tool_calls"]:
                    for tool_call in response["tool_calls"]:
                        self._execute_tool_call(tool_call)
                else:
                    success = True  # <-- FIX: Set success before returning
                    final_output = response["content"]
                    return response["content"]

            raise RuntimeError(
                f"Agent exceeded maximum iterations ({max_iterations}). "
                "This usually means the agent is stuck in a loop."
            )
        except Exception as e:
            final_output = str(e)
            raise
        finally:
            self.obs.finalize_run(success, final_output)

    def _execute_tool_call(self, tool_call: dict) -> None:
        function_name = tool_call["function"]["name"]

        start_time = time.time()
        success = False
        error_msg = None

        try:
            arguments = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError as e:
            print(f"  [ERR] Invalid JSON from LLM: {e}")
            error_msg = f"Invalid JSON: {str(e)}"
            self.history.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": f"Error: The arguments provided were not valid JSON. Error details: {str(e)}",
            })
            # Track the failure
            latency = time.time() - start_time
            self.obs.track_tool_execution(
                tool_name=function_name,
                arguments={},
                success=False,
                latency=latency,
                error=error_msg
            )
            return

        print(f"Calling tool: {function_name}({arguments})")

        if function_name not in self.tools:
            result = f"Error: Tool '{function_name}' not found"
            error_msg = result
        else:
            try:
                tool = self.tools[function_name]
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
                    error_msg = "User denied"
                    print("[DENIED] User rejected the action")
                else:
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            arguments["project_root"] = self.project_root
                            result = tool.execute(**arguments)
                            success = True
                            print(f"  [OK] Result: {str(result)[:200]}...")
                            break
                        except Exception as e:
                            error_msg = str(e)
                            print(
                                f"  [ERR] Attempt {attempt + 1}/{max_retries} failed: {error_msg[:100]}")
                            if attempt == max_retries - 1:
                                result = f"Tool '{function_name}' failed after {max_retries} attempts. Last error: {error_msg}"
                            else:
                                result = f"Error: {error_msg}. Please correct your arguments and try again."
                                self.history.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "content": result,
                                })
                                # Track the retry failure
                                latency = time.time() - start_time
                                self.obs.track_tool_execution(
                                    tool_name=function_name,
                                    arguments=arguments,
                                    success=False,
                                    latency=latency,
                                    error=error_msg
                                )
                                return
            except Exception as e:
                result = f"Critical error executing tool: {str(e)}"
                error_msg = result
                print(f"  [CRITICAL] {result}")

        # Track the final result (success or failure)
        latency = time.time() - start_time
        self.obs.track_tool_execution(
            tool_name=function_name,
            arguments=arguments,
            success=success,
            latency=latency,
            error=error_msg
        )

        # HARD TRUNCATION: The real hero of token management
        result_str = str(result)
        if len(result_str) > 800:
            result_str = result_str[:800] + \
                "\n\n...[OUTPUT TRUNCATED TO 800 CHARS TO SAVE TOKENS]..."

        self.history.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": result_str,
        })

    def reset(self) -> None:
        self.history = []
