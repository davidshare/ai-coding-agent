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

    def _compress_history(self) -> None:
        """Safely compress the middle of the history without triggering 413 errors."""
        if len(self.history) <= 12:
            return  # Not large enough to warrant compression

        print("  [MEMORY] Compressing middle history to save tokens...")

        system_msg = self.history[0]
        first_user_msg = next(
            (msg for msg in self.history if msg["role"] == "user"), None)
        recent_messages = self.history[-4:]
        middle_messages = self.history[1:-4]

        # Remove first_user_msg from middle if it's there, so we don't summarize it twice
        if first_user_msg and first_user_msg in middle_messages:
            middle_messages.remove(first_user_msg)

        # SAFETY: Truncate the middle text BEFORE sending to the summarizer
        # to guarantee we don't hit the 7000-token input limit during compression.
        summary_text = ""
        for msg in middle_messages:
            content = str(msg.get("content", ""))
            if len(content) > 400:
                content = content[:400] + "...[truncated for summary]..."
            summary_text += f"{msg['role']}: {content}\n"

        prompt = (
            "Summarize the following agent conversation history into a single, concise paragraph. "
            "Preserve crucial facts, file paths, created files, and current task status. "
            "Keep it strictly under 150 words.\n\n"
            f"History:\n{summary_text}"
        )

        try:
            # Call LLM to summarize. Because we truncated the input, this is safe from 413 errors.
            response = self.llm.complete(
                messages=[{"role": "user", "content": prompt}])
            summary_content = response.get("content", "History summarized.")

            # Rebuild history: System + First User + Summary + Recent
            self.history = [system_msg]
            if first_user_msg:
                self.history.append(first_user_msg)

            self.history.append({
                "role": "system",
                "content": f"SUMMARY OF PAST ACTIONS: {summary_content}"
            })

            self.history.extend(recent_messages)
            print("  [MEMORY] Compression successful.")

        except Exception as e:
            print(
                f"  [MEMORY] Compression failed ({e}). Falling back to trimming oldest messages.")
            # Fallback: If compression fails, just drop the oldest middle messages
            self.history = [system_msg]
            if first_user_msg:
                self.history.append(first_user_msg)
            self.history.extend(recent_messages)

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

            # TRIGGER COMPRESSION: Only when history gets genuinely large
            if len(self.history) > 12:
                self._compress_history()

            print(
                f"\n[Iteration {iteration}] (History length: {len(self.history)})")

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

        try:
            arguments = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError as e:
            print(f"  [ERR] Invalid JSON from LLM: {e}")
            self.history.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": f"Error: The arguments provided were not valid JSON. Error details: {str(e)}",
            })
            return

        print(f"Calling tool: {function_name}({arguments})")

        if function_name not in self.tools:
            result = f"Error: Tool '{function_name}' not found"
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
                    print("[DENIED] User rejected the action")
                else:
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            arguments["project_root"] = self.project_root
                            result = tool.execute(**arguments)
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
                                return
            except Exception as e:
                result = f"Critical error executing tool: {str(e)}"
                print(f"  [CRITICAL] {result}")

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
