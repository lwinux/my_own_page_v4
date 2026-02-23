import os


class Config:
    SECRET_KEY: str = os.environ.get("SECRET_KEY")
    BACKEND_URL: str = os.environ.get("BACKEND_URL", "http://localhost:8000")
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"
