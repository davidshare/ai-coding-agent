"""Simple hello script demonstrating project coding standards."""

from __future__ import annotations

from dataclasses import dataclass


class GreetingError(Exception):
    """Base exception for greeting-related errors."""


@dataclass
class Greeting:
    """A personalized greeting message.

    Args:
        name: The person to greet.
        message: The greeting text.
    """

    name: str
    message: str

    def render(self) -> str:
        """Return the greeting formatted as a display string.

        Returns:
            The formatted greeting message.
        """
        return f"{self.message}, {self.name}!"


def greet(name: str) -> str:
    """Build a greeting message for the given name.

    Args:
        name: The person to greet. Must be non-empty.

    Returns:
        A personalized greeting string.

    Raises:
        GreetingError: If ``name`` is empty or whitespace only.
    """
    if not name.strip():
        raise GreetingError("name must not be empty")

    greeting = Greeting(name=name, message="Hello")
    return greeting.render()


def main() -> None:
    """Print a greeting to the console."""
    print(greet("World"))


if __name__ == "__main__":
    main()