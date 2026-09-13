import time

from groq import Groq

from config import Config


class LLMclient:
    def __init__(self, config: Config):
        self.client = Groq(api_key=config.groq_api_key)
        self.model = config.model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature

    def complete(
            self,
            messages: list[dict],
            tools: list[dict] | None = None
    ) -> dict:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # Retry loop for rate limits
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(**kwargs)
                break  # Success, exit the retry loop
            except Exception as e:
                error_str = str(e).lower()
                # Check if it's a Groq rate limit error and we have retries left
                if "rate_limit_exceeded" in error_str and attempt < 2:
                    wait_time = 2 ** attempt  # Waits 1s, then 2s
                    print(
                        f"  [RATE LIMIT] Hit OTPM limit. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    # Not a rate limit, or final attempt failed. Let the outer except handle it.
                    raise

        try:
            message = response.choices[0].message

            content = message.content if message.content is not None else ""
            role = message.role if message.role is not None else "assistant"
            result = {
                "role": role,
                "content": content,
            }

            if hasattr(message, "tool_calls") and message.tool_calls:
                tool_calls_list = []
                for tc in message.tool_calls:
                    tool_calls_list.append({
                        "id": tc.id,
                        "type": tc.type if hasattr(tc, "type") else "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    })
                if tool_calls_list:
                    result["tool_calls"] = tool_calls_list

            return result

        except Exception as e:
            print(f"LLM API error: {e}")
            return {
                "role": "assistant",
                "content": f"Error calling LLM: {str(e)}",
            }
