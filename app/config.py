from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Storefront API"
    environment: str = "development"
    debug: bool = True

    secret_key: str = "change-this-to-a-long-random-string"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    database_url: str = "sqlite:///./database.db"

    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 5

    # Optional: if set, main.py creates this admin automatically at startup
    # if no admin exists yet in the database. Leave unset to disable.
    admin_username: str | None = None
    admin_password: str | None = None
    admin_role: str = "super_admin"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
