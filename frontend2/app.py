from app import create_app

app = create_app()

if __name__ == "__main__":
    import os

    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5002, debug=debug)
