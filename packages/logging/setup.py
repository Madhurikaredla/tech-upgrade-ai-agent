import logging

import logfire

from packages.config.settings import get_settings

_configured = False


def configure_logfire() -> None:
    """Configure logfire once. Safe to call multiple times."""
    global _configured
    if _configured:
        return
    _configured = True

    settings = get_settings()

    if not settings.logfire_token:
        logfire.configure(
            service_name=settings.app_name,
            service_version=settings.app_version,
            send_to_logfire=False,
            inspect_arguments=False,
            console=logfire.ConsoleOptions(colors="auto", include_timestamps=True),
        )
    else:
        logfire.configure(
            service_name=settings.app_name,
            service_version=settings.app_version,
            token=settings.logfire_token.get_secret_value(),
            send_to_logfire=True,
            inspect_arguments=False,
            console=logfire.ConsoleOptions(colors="auto", include_timestamps=True),
        )
        logfire.instrument_pydantic_ai()
        logfire.instrument_httpx()

    # Bridge Python stdlib logging (used by uvicorn, httpx, etc.) into logfire
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logfire.LogfireLoggingHandler()],
    )
