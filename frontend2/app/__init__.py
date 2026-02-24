import logging

from flask import Flask, redirect, render_template
from app.config import Config

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    flask_app = Flask(__name__, template_folder="../templates", static_folder="../static")
    flask_app.config.from_object(Config)

    from app.routes.public import public_bp

    flask_app.register_blueprint(public_bp)

    @flask_app.get("/")
    def index():
        return redirect("/app")

    @flask_app.get("/health")
    def health():
        return {"status": "ok", "service": "frontend2"}

    @flask_app.errorhandler(404)
    def not_found(e):
        return render_template("errors/not_found.html"), 404

    @flask_app.errorhandler(500)
    def server_error(e):
        logger.exception("Unhandled error: %s", e)
        return render_template("errors/not_found.html"), 500

    return flask_app
