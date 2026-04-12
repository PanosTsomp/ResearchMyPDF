# Ollama implementation of LLMProvider.
# Talks to a locally running Ollama instance.

import ollama


class OllamaProvider:
    def __init__(self, model: str = "llama3.2"):
        self.model = model

    def summarize(self, prompt: str) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]