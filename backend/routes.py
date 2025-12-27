from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash
from backend.db import get_db

health_bp = Blueprint("health", __name__)
auth_bp = Blueprint("auth", __name__)

@health_bp.route("/health")
def health():
    try:
        db = get_db()
        db.execute("SELECT 1")
        db.close()
        return jsonify(status="ok", db="connected")
    except Exception as e:
        return jsonify(status="error", error=str(e)), 500


@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username=? AND role='admin' AND is_active=1",
        (username,)
    ).fetchone()
    db.close()

    if not user:
        return jsonify(error="Invalid credentials"), 401

    if not check_password_hash(user["password_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    return jsonify(message="Admin login successful", admin_id=user["id"])

