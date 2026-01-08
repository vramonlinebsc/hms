# ROUTES VERSION: patient auth removed (CI sync)

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash
from backend.db import get_db
from backend.config import SECRET_KEY, JWT_ALGO, JWT_EXP_SECONDS
from datetime import datetime, timedelta
import jwt
from functools import wraps

health_bp = Blueprint("health", __name__)
auth_bp = Blueprint("auth", __name__)


# =========================
# AUTH UTIL
# =========================
def make_token(user_id, role):
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_SECONDS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGO)


def require_role(expected_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify(error="Missing or invalid Authorization header"), 401

            token = auth_header.split(" ", 1)[1]

            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGO])
            except jwt.ExpiredSignatureError:
                return jsonify(error="Token expired"), 401
            except Exception:
                return jsonify(error="Invalid token"), 401

            if payload.get("role") != expected_role:
                return jsonify(error="Forbidden"), 403

            request.user_id = int(payload["sub"])
            request.user_role = payload["role"]

            return fn(*args, **kwargs)
        return wrapper
    return decorator


# =========================
# HEALTH
# =========================
@health_bp.route("/health", methods=["GET"])
def health():
    db = get_db()
    db.execute("SELECT 1")
    return jsonify(status="ok", db="connected")


# =========================
# ADMIN AUTH
# =========================
@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify(error="Username and password required"), 400

    db = get_db()
    row = db.execute(
        "SELECT id, password_hash FROM users WHERE username=? AND role='admin' AND is_active=1",
        (username,)
    ).fetchone()

    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    token = make_token(row["id"], "admin")

    return jsonify(
        admin_id=row["id"],
        token=token,
        message="Admin login successful"
    )


@auth_bp.route("/admin/me", methods=["GET"])
@require_role("admin")
def admin_me():
    return jsonify(admin_id=request.user_id, role="admin")


# =========================
# DOCTOR AUTH
# =========================
@auth_bp.route("/doctor/login", methods=["POST"])
def doctor_login():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify(error="Username and password required"), 400

    db = get_db()
    row = db.execute(
        """
        SELECT u.id, u.password_hash, d.is_blacklisted
        FROM users u
        JOIN doctors d ON d.user_id = u.id
        WHERE u.username = ?
          AND u.role = 'doctor'
          AND u.is_active = 1
        """,
        (username,)
    ).fetchone()

    if not row:
        return jsonify(error="Invalid credentials"), 401

    if row["is_blacklisted"]:
        return jsonify(error="Doctor is blacklisted"), 403

    if not check_password_hash(row["password_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    token = make_token(row["id"], "doctor")

    return jsonify(
        doctor_id=row["id"],
        token=token,
        message="Doctor login successful"
    )


@auth_bp.route("/doctor/me", methods=["GET"])
@require_role("doctor")
def doctor_me():
    return jsonify(doctor_id=request.user_id, role="doctor")

