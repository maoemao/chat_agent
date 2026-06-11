from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = ""
    VOLC_API_KEY: str = ""
    VOLC_ACCESS_KEY: str = ""
    VOLC_SECRET_KEY: str = ""
    GITHUB_TOKEN: str = ""
    RAG_DOCS_PATH: str = "data/documents"
    DATABASE_URL: str = "sqlite:///./app.db"
    MCP_CONFIG_PATH: str = "config/mcp_config.json"
    ENABLED_ADAPTERS: str = "telegram"
    USE_MOCK_AI: bool = False
    
    @property
    def rag_docs_path(self) -> Path:
        return Path(self.RAG_DOCS_PATH)
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()