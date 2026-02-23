import os


class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY")
    BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://localhost:8000")
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    SESSION_COOKIE_SECURE: bool = (
        os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    )
    PERMANENT_SESSION_LIFETIME: int = 60 * 60 * 24 * 7  # 7 days
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"
