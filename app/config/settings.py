from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "FastIQ"
    APP_ENV: str = "local"
    DEBUG: bool = True
    PORT: int = 8000
    DATABASE_URL: str
    SECRET_KEY: str

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local", ".env.production"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
