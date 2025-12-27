from flask import Flask
from backend.routes import health_bp,auth_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

