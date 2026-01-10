from flask import Flask
from flask_cors import CORS

from backend.db import init_app
from backend.rate_limit import rate_limiter

# Explicit blueprints
from backend.routes import health_bp, auth_bp
from backend.routes_patient import patient_bp
from backend.routes_doctor import doctor_bp
from backend.routes_admin import admin_bp
from backend.metrics import metrics_bp

from flask import g




def create_app():
    app = Flask(__name__)
    @app.teardown_appcontext
    def close_db(exception):
        db = g.pop("db", None)
        if db is not None:
            db.close()
    CORS(app)

    # DB wiring ONLY (no schema creation here)
    init_app(app)

    # Infra middleware
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

    # Blueprint wiring (authoritative)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(metrics_bp)

    return app


if __name__ == "__main__":
    from backend.init_db import init_db
    init_db()  # only for manual runs
    app = create_app()
    app.run(debug=True)

