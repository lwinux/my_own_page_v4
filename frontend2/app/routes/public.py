import re

from flask import Blueprint, render_template

from app.api_client import get_client

public_bp = Blueprint("public", __name__)

# Token is 64 hex chars (secrets.token_hex(32))
_TOKEN_RE = re.compile(r"^(.+)-([0-9a-f]{64})$")


@public_bp.get("/<path:slug_with_token>")
def view_profile(slug_with_token: str):
    """
    Route: /<profile_slug>-<64-char-hex-token>
    Fetches profile data from backend and renders the public landing page.
    """
    match = _TOKEN_RE.match(slug_with_token)
    if not match:
        return render_template("errors/not_found.html"), 404

    token = match.group(2)
    profile_data = get_client().get_profile(token)

    if profile_data is None:
        return render_template("errors/not_found.html"), 404

    return render_template("profile/view.html", profile=profile_data)
