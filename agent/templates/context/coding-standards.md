---
version: 1.0.0
last_updated: 2026-09-14
---

# Coding Standards

## Language
- Python 3.11+
- Use type hints on all function signatures
- Use dataclasses for data-holding classes

## Style
- Follow PEP 8
- Maximum line length: 88 characters
- Use double quotes for strings
- Use f-strings for formatting

## Naming
- Functions and variables: snake_case
- Classes: PascalCase
- Constants: UPPER_SNAKE_CASE
- Private members: prefix with underscore

## Error Handling
- Use custom exception classes (inherit from Exception)
- Never use bare `except:` — always catch specific exceptions
- Log errors with context before re-raising

## Documentation
- Every public function must have a docstring
- Docstrings follow Google style
- Include Args, Returns, and Raises sections