"""
Backend API client for frontend1 (server-side BFF pattern).

Tokens are stored in Flask session.
On 401, the client automatically attempts a token refresh before retrying.
"""
import httpx
from flask import session, current_app


class APIError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")


class BackendClient:
    def __init__(self) -> None:
        self.base_url: str = current_app.config["BACKEND_URL"]
        self._timeout = httpx.Timeout(30.0)

    # ── Auth helpers ──────────────────────────────────────────────────────────

    def _auth_headers(self) -> dict[str, str]:
        token = session.get("access_token")
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def _try_refresh(self) -> bool:
        refresh_token = session.get("refresh_token")
        if not refresh_token:
            return False
        try:
            resp = httpx.post(
                f"{self.base_url}/api/auth/refresh",
                json={"refresh_token": refresh_token},
                timeout=self._timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                session["access_token"] = data["access_token"]
                session["refresh_token"] = data["refresh_token"]
                return True
        except httpx.RequestError:
            pass
        return False

    # ── Generic request ───────────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        *,
        raise_on_error: bool = True,
        **kwargs,
    ) -> httpx.Response:
        url = f"{self.base_url}{path}"
        headers = {**self._auth_headers(), **kwargs.pop("headers", {})}

        resp = httpx.request(method, url, headers=headers, timeout=self._timeout, **kwargs)

        if resp.status_code == 401 and self._try_refresh():
            headers = {**self._auth_headers(), **kwargs.pop("headers", {})}
            resp = httpx.request(method, url, headers=headers, timeout=self._timeout, **kwargs)

        if raise_on_error and resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise APIError(resp.status_code, detail)

        return resp

    # ── Convenience wrappers ──────────────────────────────────────────────────

    def get(self, path: str, **kwargs) -> httpx.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> httpx.Response:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> httpx.Response:
        return self._request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs) -> httpx.Response:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> httpx.Response:
        return self._request("DELETE", path, **kwargs)

    # ── Auth flows ────────────────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        resp = httpx.post(
            f"{self.base_url}/api/auth/login",
            json={"email": email, "password": password},
            timeout=self._timeout,
        )
        if resp.status_code != 200:
            detail = resp.json().get("detail", "Login failed")
            raise APIError(resp.status_code, detail)
        data = resp.json()
        session["access_token"] = data["access_token"]
        session["refresh_token"] = data["refresh_token"]
        session["user_id"] = data["user_id"]
        session["username"] = data["username"]
        session.permanent = True
        return data

    def register(self, email: str, username: str, password: str) -> dict:
        resp = httpx.post(
            f"{self.base_url}/api/auth/register",
            json={"email": email, "username": username, "password": password},
            timeout=self._timeout,
        )
        if resp.status_code not in (200, 201):
            detail = resp.json().get("detail", "Registration failed")
            raise APIError(resp.status_code, detail)
        return resp.json()

    def logout(self) -> None:
        try:
            httpx.post(f"{self.base_url}/api/auth/logout", timeout=self._timeout)
        except Exception:
            pass
        session.clear()


def get_client() -> BackendClient:
    return BackendClient()
