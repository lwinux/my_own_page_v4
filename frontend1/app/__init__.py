from flask import Flask, redirect
from app.config import Config


def create_app() -> Flask:
    flask_app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/app/static",
    )
    flask_app.config.from_object(Config)

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.editor import editor_bp

    flask_app.register_blueprint(auth_bp, url_prefix="/app")
    flask_app.register_blueprint(dashboard_bp, url_prefix="/app")
    flask_app.register_blueprint(editor_bp, url_prefix="/app")

    @flask_app.get("/")
    def index():
        return redirect("/app")

    @flask_app.get("/app/health")
    def health():
        return {"status": "ok", "service": "frontend1"}

    return flask_app
