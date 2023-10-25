"""Overrides for tests."""

from datetime import time
from functools import lru_cache

import config


@lru_cache
def override_get_settings() -> config.Settings:
    return config.Settings(
        # SQLALCHEMY_DATABASE_URL="postgresql+psycopg://postgres@localhost/bongo",
        SQLALCHEMY_DATABASE_URL="sqlite:///./test.db",
        VOTING_ENDS_AT=time(9),
    )


config.get_settings = override_get_settings
