from flask import Flask
from app.config import Config


def create_app() -> Flask:
    flask_app = Flask(__name__, template_folder="../templates", static_folder="../static")
    flask_app.config.from_object(Config)

    from app.routes.public import public_bp

    flask_app.register_blueprint(public_bp)

    @flask_app.get("/health")
    def health():
        return {"status": "ok", "service": "frontend2"}

    return flask_app
