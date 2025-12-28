from flask import Flask
from backend.routes import health_bp, auth_bp
from backend.init_db import init_db

init_db()

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "dev-secret-change-later"
    app.config["JWT_ALGO"] = "HS256"
    app.config["JWT_EXP_SECONDS"] = 3600  # 1 hour

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

