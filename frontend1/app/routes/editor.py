import json

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from app.api_client import APIError, get_client
from app.routes.auth import login_required

editor_bp = Blueprint("editor", __name__)


@editor_bp.get("/profiles/<profile_id>/edit")
@login_required
def edit(profile_id: str):
    client = get_client()
    try:
        profile = client.get(f"/api/profiles/{profile_id}").json()
        draft_resp = client.get(f"/api/profiles/{profile_id}/draft", raise_on_error=False)
        draft = draft_resp.json().get("draft") if draft_resp.status_code == 200 else None
    except APIError as e:
        flash(f"Failed to load profile: {e.detail}", "error")
        return redirect(url_for("dashboard.index"))

    return render_template(
        "editor/index.html",
        profile=profile,
        draft_json=json.dumps(draft) if draft else "null",
    )


# ── AJAX endpoints (called by editor.js) ────────────────────────────────────

@editor_bp.post("/profiles/<profile_id>/draft")
@login_required
def save_draft(profile_id: str):
    """Receive draft JSON from the editor and forward to backend."""
    body = request.get_json(force=True, silent=True)
    if not body:
        return jsonify({"error": "Invalid JSON body"}), 400

    try:
        resp = get_client().put(f"/api/profiles/{profile_id}/draft", json=body)
        return jsonify({"ok": True, "draft": resp.json().get("draft")}), 200
    except APIError as e:
        return jsonify({"error": e.detail}), e.status_code


@editor_bp.post("/profiles/<profile_id>/publish")
@login_required
def publish(profile_id: str):
    """Trigger publish and return the public URL."""
    try:
        resp = get_client().post(f"/api/profiles/{profile_id}/publish")
        return jsonify(resp.json()), 201
    except APIError as e:
        return jsonify({"error": e.detail}), e.status_code


@editor_bp.delete("/profiles/<profile_id>/draft")
@login_required
def discard_draft(profile_id: str):
    try:
        get_client().delete(f"/api/profiles/{profile_id}/draft", raise_on_error=False)
        return jsonify({"ok": True}), 200
    except APIError as e:
        return jsonify({"error": e.detail}), e.status_code
