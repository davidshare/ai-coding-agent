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

        try:
            response = self.client.chat.completions.create(**kwargs)
            # print(f"Raw response type: {type(response)}")

            message = response.choices[0].message
            # print(f"Message attributes: {dir(message)}")

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

            # print(f"LLM response received (content length: {len(content)})")
            return result
        except Exception as e:
            print(f"LLM API error: {e}")
            return {
                "role": "assistant",
                "content": f"Error calling LLM: {str(e)}",
            }
