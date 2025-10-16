from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field


class Settings(BaseSettings):
    # === General ===
    env: str
    log_level: str

    # === Base de datos ===
    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str

    @computed_field
    @property
    def database_url(self) -> str:
        """Construye automáticamente la URL para SQLAlchemy/Alembic"""
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # === Redis / Celery ===
    redis_url: str
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    # === Scraping ===
    scrape_limit: int
    scrape_timeout: int

    # === NLP ===
    spacy_model: str
    transformers_model: str

    # === Notificaciones (Slack) ===
    slack_webhook_url: str | None = None
    slack_channel: str | None = None
    slack_bot_token: str | None = None

    # === Rutas locales ===
    reports_dir: str
    graphs_dir: str
    logs_dir: str

    # === API (FastAPI/Uvicorn) ===
    api_host: str
    api_port: int

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Instancia global de settings
settings = Settings()

if __name__ == "__main__":
    from pprint import pprint

    print("✅ Configuración cargada desde .env:")
    pprint(settings.model_dump())
