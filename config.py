from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    USERNAME_MIN_LENGTH: int
    USERNAME_MAX_LENGTH: int
    PASSWORD_MIN_LENGTH: int
    PASSWORD_MAX_LENGTH: int
    JWT_TTL_SECONDS: int
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ROOT_USERNAME: str = "root"
    ROOT_PASSWORD: str = ""
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./db.sqlite3"


settings = Settings.model_validate({})
