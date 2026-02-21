from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.api_client import APIError, get_client

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    """Decorator — redirect to login if not authenticated."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("access_token"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


@auth_bp.get("/login")
def login():
    if session.get("access_token"):
        return redirect(url_for("dashboard.index"))
    return render_template("auth/login.html")


@auth_bp.post("/login")
def login_post():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Email and password are required.", "error")
        return render_template("auth/login.html"), 400

    try:
        get_client().login(email, password)
        return redirect(url_for("dashboard.index"))
    except APIError as e:
        flash(e.detail, "error")
        return render_template("auth/login.html", email=email), 400


@auth_bp.get("/register")
def register():
    if session.get("access_token"):
        return redirect(url_for("dashboard.index"))
    return render_template("auth/register.html")


@auth_bp.post("/register")
def register_post():
    email = request.form.get("email", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    if password != confirm:
        flash("Passwords do not match.", "error")
        return render_template("auth/register.html", email=email, username=username), 400

    try:
        get_client().register(email, username, password)
        get_client().login(email, password)
        return redirect(url_for("dashboard.index"))
    except APIError as e:
        flash(e.detail, "error")
        return render_template("auth/register.html", email=email, username=username), 400


@auth_bp.post("/logout")
def logout():
    get_client().logout()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
