from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    USERNAME_MIN_LENGTH: int
    USERNAME_MAX_LENGTH: int
    PASSWORD_MIN_LENGTH: int
    PASSWORD_MAX_LENGTH: int
    JWT_TTL_SECONDS: int
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./db.sqlite3"
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
