"""Centralised model factory.

Returns the correct pydantic-ai model based on which API keys are configured.
Priority: Azure OpenAI → Google Gemini → Groq → Anthropic → raises if none is set.

Usage:
    from packages.config.model_factory import get_model
    agent = Agent(model=get_model(), ...)
"""

from urllib.parse import urlparse

from pydantic_ai.models import Model

from .settings import Settings, get_settings


def get_model(settings: Settings | None = None) -> Model:
    s = settings or get_settings()

    if s.azure_openai_model_endpoint and s.azure_openai_model_key:
        from openai import AsyncAzureOpenAI
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider

        parsed = urlparse(s.azure_openai_model_endpoint)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        # path: /openai/deployments/<deployment>/chat/completions
        path_parts = [p for p in parsed.path.split("/") if p]
        deployment = path_parts[2] if len(path_parts) > 2 else "gpt-4o-mini"

        client = AsyncAzureOpenAI(
            azure_endpoint=base_url,
            azure_deployment=deployment,
            api_key=s.azure_openai_model_key.get_secret_value(),
            api_version=s.azure_openai_model_api_version,
        )
        return OpenAIModel(deployment, provider=OpenAIProvider(openai_client=client))

    if s.google_api_key:
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider

        return GoogleModel(
            s.default_model,
            provider=GoogleProvider(api_key=s.google_api_key.get_secret_value()),
        )

    if s.groq_api_key:
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider

        return OpenAIModel(
            s.groq_model,
            provider=OpenAIProvider(
                base_url="https://api.groq.com/openai/v1",
                api_key=s.groq_api_key.get_secret_value(),
            ),
        )

    if s.anthropic_api_key:
        from pydantic_ai.models.anthropic import AnthropicModel

        return AnthropicModel(s.default_model)

    raise RuntimeError(
        "No AI provider configured. Set AZURE_OPENAI_MODEL_ENDPOINT + AZURE_OPENAI_MODEL_KEY, "
        "GOOGLE_API_KEY, or GROQ_API_KEY in your .env file."
    )
