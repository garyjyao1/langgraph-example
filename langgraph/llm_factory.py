import os

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_openrouter import ChatOpenRouter

_DEFAULT_MODELS = {
    "ollama": "llama3.2",
    "openai": "gpt-4.1-nano",
    "gemini": "gemini-2.5-flash",
    "anthropic": "claude-sonnet-4-6",
    "azure": "gpt-4o",
    "meta": "Llama-4-Scout-17B-16E-Instruct",
    "deepseek": "deepseek-chat",
    "mistral": "mistral-large-latest",
    "xai": "grok-3-mini",
    "openrouter": "openrouter/auto",
}

_PROVIDERS = {
    "ollama": (
        ChatOpenAI,
        {
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "openai": (
        ChatOpenAI,
        {
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "gemini": (
        ChatGoogleGenerativeAI,
        {
            "api_key": os.environ.get("GEMINI_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "anthropic": (
        ChatAnthropic,
        {
            "api_key": os.environ.get("ANTHROPIC_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "azure": (
        AzureChatOpenAI,
        {
            "azure_endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT"),
            "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
            "api_version": os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "meta": (
        ChatOpenAI,
        {
            "base_url": "https://api.llama.com/compat/v1",
            "api_key": os.environ.get("LLAMA_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "deepseek": (
        ChatOpenAI,
        {
            "base_url": "https://api.deepseek.com/v1",
            "api_key": os.environ.get("DEEPSEEK_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "mistral": (
        ChatMistralAI,
        {
            "api_key": os.environ.get("MISTRAL_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "xai": (
        ChatOpenAI,
        {
            "base_url": "https://api.x.ai/v1",
            "api_key": os.environ.get("XAI_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
    "openrouter": (
        ChatOpenRouter,
        {
            "api_key": os.environ.get("OPENROUTER_API_KEY"),
            "temperature": 0.7,
            "max_tokens": 4096,
        },
    ),
}


def create_llm(provider: str = None):
    provider = provider or os.environ.get("LLM_PROVIDER", "ollama")
    if provider not in _PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")
    model = os.environ.get("LLM_MODEL") or _DEFAULT_MODELS[provider]
    print(f"Creating LLM, provider={provider}, model={model}")
    cls, kwargs = _PROVIDERS[provider]
    return cls(model=model, **kwargs)
