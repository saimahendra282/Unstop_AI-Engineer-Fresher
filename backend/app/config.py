from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    mongo_uri: str = Field("mongodb://localhost:27017", env="MONGO_URI")
    mongo_db: str = Field("support_ai", env="MONGO_DB")
    # Gmail API Configuration (replaces IMAP)
    gmail_credentials_path: str | None = Field(None, env="GMAIL_CREDENTIALS_PATH")
    gmail_token_path: str | None = Field(None, env="GMAIL_TOKEN_PATH")
    gmail_user: str | None = Field(None, env="GMAIL_USER")
    # SMTP for sending replies
    smtp_host: str | None = Field(None, env="SMTP_HOST")
    smtp_port: int | None = Field(587, env="SMTP_PORT")
    smtp_user: str | None = Field(None, env="SMTP_USER")
    smtp_password: str | None = Field(None, env="SMTP_PASSWORD")
    gemini_api_key: str | None = Field(None, env="GEMINI_API_KEY")
    embeddings_model: str = Field("all-MiniLM-L6-v2", env="EMBEDDINGS_MODEL")
    rag_top_k: int = Field(3, env="RAG_TOP_K")
    response_temperature: float = Field(0.4, env="RESPONSE_TEMPERATURE")
    allowed_origins: str = Field("*", env="ALLOWED_ORIGINS")
    csv_path: str = Field(str(Path(__file__).resolve().parents[2] / "68b1acd44f393_Sample_Support_Emails_Dataset.csv"), env="CSV_PATH")

@lru_cache
def get_settings() -> Settings:
    return Settings()
