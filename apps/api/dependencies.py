from packages.client.nestjs_client import NestJSClient
from packages.config.settings import Settings, get_settings

from .repositories.session_repository import SessionRepository


def get_app_settings() -> Settings:
    return get_settings()


async def get_nestjs_client() -> NestJSClient:
    return await NestJSClient.get_instance()


def get_session_repository() -> SessionRepository:
    return SessionRepository()
