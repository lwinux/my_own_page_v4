from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.api_client import APIError, get_client
from app.routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
@login_required
def index():
    try:
        profiles = get_client().get("/api/profiles").json()
    except APIError as e:
        if e.status_code == 401:
            return redirect(url_for("auth.login"))
        flash(f"Failed to load profiles: {e.detail}", "error")
        profiles = []
    return render_template(
        "dashboard/index.html",
        profiles=profiles,
        username=session.get("username"),
    )


@dashboard_bp.post("/profiles/create")
@login_required
def create_profile():
    profile_name = request.form.get("profile_name", "").strip()
    company_note = request.form.get("company_note", "").strip()

    if not profile_name:
        flash("Profile name is required.", "error")
        return redirect(url_for("dashboard.index"))

    try:
        profile = get_client().post(
            "/api/profiles",
            json={"profile_name": profile_name, "company_note": company_note},
        ).json()
        flash(f'Profile "{profile_name}" created.', "success")
        return redirect(url_for("editor.edit", profile_id=profile["id"]))
    except APIError as e:
        flash(f"Could not create profile: {e.detail}", "error")
        return redirect(url_for("dashboard.index"))


@dashboard_bp.post("/profiles/<profile_id>/update")
@login_required
def update_profile(profile_id: str):
    profile_name = request.form.get("profile_name", "").strip()
    company_note = request.form.get("company_note", "").strip()

    try:
        get_client().patch(
            f"/api/profiles/{profile_id}",
            json={"profile_name": profile_name or None, "company_note": company_note},
        )
        flash("Profile updated.", "success")
    except APIError as e:
        flash(f"Update failed: {e.detail}", "error")

    return redirect(url_for("dashboard.index"))
