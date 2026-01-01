from flask import Flask
from flask_cors import CORS

from backend.routes import health_bp, auth_bp
from backend.routes_admin import admin_bp
from backend.metrics import metrics_bp
from backend.init_db import init_db
from backend.rate_limit import rate_limiter
from backend.db import init_app
from backend.routes_doctor import doctor_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.before_request
    def apply_rate_limit():
        limited = rate_limiter()
        if limited:
            return limited
        return None

    @app.after_request
    def add_audit_headers(response):
        response.headers["X-Service"] = "HMS"
        response.headers["X-Version"] = "1.0"
        response.headers["X-Environment"] = "dev"
        return response

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(metrics_bp)

    init_app(app)

    return app


if __name__ == "__main__":
    init_db()
    app = create_app()
    app.run(debug=True)
