from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    USERNAME_MIN_LENGTH: int = 3
    USERNAME_MAX_LENGTH: int = 32
    PASSWORD_MIN_LENGTH: int = 6
    PASSWORD_MAX_LENGTH: int = 18
    JWT_TTL_SECONDS: int = 3600
    JWT_SECRET_KEY: str = (
        "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )
    JWT_ALGORITHM: str = "HS256"
    ROOT_USERNAME: str = "root"
    ROOT_PASSWORD: str = ""
    ROOT_EMAIL: str = "root@email.com"
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./db.sqlite3"


settings = Settings.model_validate({})
