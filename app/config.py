from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    openai_api_key: str
    tavily_api_key: str

    langchain_api_key: str = ""
    langchain_tracing_v2: bool = True
    langchain_project: str = "CRAG"

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_db_url: str

    chroma_persist_directory: str = "./.chroma_db"
    chroma_collection_name: str = "rag-chroma"


@lru_cache
def get_settings() -> Settings:
    return Settings()
