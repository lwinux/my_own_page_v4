import httpx
from flask import current_app


class PublicAPIClient:
    def __init__(self) -> None:
        self.base_url: str = current_app.config["BACKEND_URL"]
        self._timeout = httpx.Timeout(10.0)

    def get_profile(self, token: str) -> dict | None:
        """Fetch public profile data from backend. Returns None if not found."""
        try:
            resp = httpx.get(
                f"{self.base_url}/api/public/{token}",
                timeout=self._timeout,
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception:
            return None


def get_client() -> PublicAPIClient:
    return PublicAPIClient()
