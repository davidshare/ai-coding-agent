import json
import time
from abc import ABC, abstractmethod

import anthropic
from groq import Groq
from openai import OpenAI

from config import Config


class BaseLLMClient(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        pass


class GroqLLMClient(BaseLLMClient):
    """Groq API client implementation."""

    def __init__(self, config: Config):
        self.client = Groq(api_key=config.api_key)
        self.model = config.model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
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
                break
            except Exception as e:
                error_str = str(e).lower()
                if "rate_limit" in error_str and attempt < 2:
                    wait_time = 2 ** attempt
                    print(
                        f"  [RATE LIMIT] Hit Groq limit. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise

        try:
            message = response.choices[0].message
            content = message.content if message.content is not None else ""
            role = message.role if message.role is not None else "assistant"

            result = {"role": role, "content": content}

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
            print(f"Groq API parsing error: {e}")
            return {"role": "assistant", "content": f"Error parsing Groq response: {str(e)}"}


class AnthropicLLMClient(BaseLLMClient):
    """Anthropic (Claude) implementation with automatic format translation."""

    def __init__(self, config: Config):
        self.client = anthropic.Anthropic(api_key=config.api_key)
        self.model = config.model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        # 1. Extract system prompt and translate message formats
        system_prompt = ""
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "assistant":
                content = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        content.append({
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["function"]["name"],
                            "input": json.loads(tc["function"]["arguments"])
                        })
                anthropic_messages.append(
                    {"role": "assistant", "content": content})
            elif msg["role"] == "tool":
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg["tool_call_id"],
                        "content": msg["content"]
                    }]
                })
            elif msg["role"] == "user":
                anthropic_messages.append(
                    {"role": "user", "content": msg["content"]})

        # 2. Translate tool schemas to Anthropic format
        anthropic_tools = None
        if tools:
            anthropic_tools = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"]["description"],
                    "input_schema": t["function"]["parameters"],
                }
                for t in tools
            ]

        # 3. Build request parameters
        request_params = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": anthropic_messages,
        }

        if anthropic_tools:
            request_params["tools"] = anthropic_tools

        # 4. Pass temperature via extra_body (the documented escape hatch for SDK 1.5.0+)
        if self.temperature is not None:
            request_params["extra_body"] = {"temperature": self.temperature}

        # 5. Make the API call with retry logic
        for attempt in range(3):
            try:
                response = self.client.messages.create(**request_params)
                break
            except Exception as e:
                error_str = str(e).lower()
                if "rate_limit" in error_str and attempt < 2:
                    wait_time = 2 ** attempt
                    print(
                        f"  [RATE LIMIT] Hit Anthropic limit. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise

        # 6. Translate Anthropic response back to standard OpenAI format
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input),
                    },
                })

        result = {"role": "assistant", "content": content}
        if tool_calls:
            result["tool_calls"] = tool_calls

        return result


class NvidiaLLMClient(BaseLLMClient):
    """NVIDIA NIM API client implementation (OpenAI compatible)."""

    def __init__(self, config: Config):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=config.api_key
        )
        self.model = config.model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        # Optional: Uncomment the block below if using reasoning models that require it
        # kwargs["extra_body"] = {
        #     "chat_template_kwargs": {"thinking": True, "reasoning_effort": "high"}
        # }

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(**kwargs)
                break
            except Exception as e:
                error_str = str(e).lower()
                if "rate_limit" in error_str and attempt < 2:
                    wait_time = 2 ** attempt
                    print(
                        f"  [RATE LIMIT] Hit NVIDIA limit. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise

        message = response.choices[0].message
        content = message.content if message.content is not None else ""

        # Handle NVIDIA-specific reasoning content if the model outputs it
        reasoning = getattr(message, "reasoning", None) or getattr(
            message, "reasoning_content", None)
        if reasoning:
            content = f"<reasoning>\n{reasoning}\n</reasoning>\n\n{content}"

        role = message.role if message.role is not None else "assistant"

        result = {"role": role, "content": content}

        if hasattr(message, "tool_calls") and message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type if hasattr(tc, "type") else "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]

        return result


def create_llm_client(config: Config) -> BaseLLMClient:
    """Factory function to create the appropriate LLM client."""
    provider = config.provider.lower()
    if provider == "anthropic":
        return AnthropicLLMClient(config)
    elif provider == "nvidia":
        return NvidiaLLMClient(config)
    elif provider == "groq":
        return GroqLLMClient(config)
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. Supported: groq, anthropic")
