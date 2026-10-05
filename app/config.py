"""Application configuration."""

from __future__ import annotations

import os


class Settings:
    """Global settings dari environment."""

    def __init__(self) -> None:
        self.port: int = int(os.getenv("PORT", "7860"))
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.timeout: float = float(os.getenv("TIMEOUT", "10.0"))
        self.max_retry: int = int(os.getenv("MAX_RETRY", "2"))
        self.ngl_endpoint: str = os.getenv(
            "NGL_ENDPOINT", "https://ngl.link/api/submit"
        )
        self.default_user_agent: str = os.getenv(
            "DEFAULT_UA",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36",
        )


settings = Settings()