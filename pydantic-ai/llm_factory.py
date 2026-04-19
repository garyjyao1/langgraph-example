import os

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

_DEFAULT_MODELS = {
    "ollama": "llama3.2",
    "openai": "gpt-4.1-nano",
}


def create_model() -> OpenAIModel:
    """Creates a PydanticAI OpenAIModel for the configured provider.

    Supports two providers:
    - ``openai``  – standard OpenAI API (requires ``OPENAI_API_KEY``)
    - ``ollama``  – local Ollama with OpenAI-compatible endpoint (default)

    Override the model name with ``LLM_MODEL``.
    """
    provider = os.environ.get("LLM_PROVIDER", "ollama")
    model_name = os.environ.get("LLM_MODEL") or _DEFAULT_MODELS.get(provider)
    if not model_name:
        raise ValueError(f"Unknown provider: {provider}. Supported: openai, ollama")

    print(f"Creating LLM, provider={provider}, model={model_name}")

    if provider == "ollama":
        oai_provider = OpenAIProvider(
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            api_key="ollama",
        )
        return OpenAIModel(model_name, provider=oai_provider)

    if provider == "openai":
        oai_provider = OpenAIProvider(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        return OpenAIModel(model_name, provider=oai_provider)

    raise ValueError(f"Unsupported provider: {provider}. Supported: openai, ollama")
