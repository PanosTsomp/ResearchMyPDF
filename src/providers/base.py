# Its a contract so any model or API can work with the app

# The contract every LLM provider must follow.
# No inheritance needed — if it has these methods, it works.

from typing import Protocol


class LLMProvider(Protocol):
    def summarize(self, prompt: str) -> str:
        """Send a prompt and return the response as a string."""
        ...