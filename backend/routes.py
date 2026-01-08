from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash
from backend.db import get_db
from backend.config import SECRET_KEY, JWT_ALGO, JWT_EXP_SECONDS
from datetime import datetime, timedelta
import jwt
from functools import wraps

# =========================
# Blueprints
# =========================

health_bp = Blueprint("health", __name__)
auth_bp = Blueprint("auth", __name__)

# =========================
# Auth / Infra
# =========================

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

            request.user_id = payload["sub"]
            request.user_role = payload["role"]

            return fn(*args, **kwargs)
        return wrapper
    return decorator


@health_bp.route("/health", methods=["GET"])
def health():
    db = get_db()
    db.execute("SELECT 1")
    return jsonify(status="ok", db="connected")

# =========================
# Admin Auth
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
        """
        SELECT id, password_hash
        FROM users
        WHERE username = ?
          AND role = 'admin'
          AND is_active = 1
        """,
        (username,)
    ).fetchone()

    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    payload = {
        "sub": str(row["id"]),
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_SECONDS),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGO)

    return jsonify(
        admin_id=row["id"],
        token=token,
        message="Admin login successful",
    )


@auth_bp.route("/admin/me", methods=["GET"])
@require_role("admin")
def admin_me():
    return jsonify(admin_id=request.user_id, role="admin")

# =========================
# Doctor Auth
# =========================

@auth_bp.route("/doctor/login", methods=["POST"])
def doctor_login():
    data = request.get_json() or {}
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
        (username,),
    ).fetchone()

    if not row:
        return jsonify(error="Invalid credentials"), 401

    if row["is_blacklisted"]:
        return jsonify(error="Doctor is blacklisted"), 403

    if not check_password_hash(row["password_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    payload = {
        "sub": str(row["id"]),
        "role": "doctor",
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_SECONDS),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGO)

    return jsonify(
        doctor_id=row["id"],
        token=token,
        message="Doctor login successful",
    )


@auth_bp.route("/doctor/me", methods=["GET"])
@require_role("doctor")
def doctor_me():
    return jsonify(doctor_id=request.user_id, role="doctor")

# =========================
# Patient Auth
# =========================

@auth_bp.route("/patient/login", methods=["POST"])
def patient_login():
    data = request.get_json(force=True)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify(error="Username and password required"), 400

    db = get_db()
    row = db.execute(
        """
        SELECT id, password_hash
        FROM users
        WHERE username = ?
          AND role = 'patient'
          AND is_active = 1
        """,
        (username,),
    ).fetchone()

    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    payload = {
        "sub": str(row["id"]),
        "role": "patient",
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_SECONDS),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGO)

    return jsonify(
        patient_id=row["id"],
        token=token,
        message="Patient login successful",
    )

# =========================
# Admin Read-Only Views
# =========================

@auth_bp.route("/admin/stats/doctors/count", methods=["GET"])
@require_role("admin")
def admin_doctor_count():
    db = get_db()
    row = db.execute("SELECT COUNT(*) AS count FROM doctors").fetchone()
    return jsonify(count=row["count"])


@auth_bp.route("/admin/stats/patients/count", methods=["GET"])
@require_role("admin")
def admin_patient_count():
    db = get_db()
    row = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'patient'
          AND is_active = 1
        """
    ).fetchone()
    return jsonify(count=row["count"])


@auth_bp.route("/admin/stats/appointments/today", methods=["GET"])
@require_role("admin")
def admin_appointments_today_count():
    db = get_db()
    row = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM appointments
        WHERE date(start_datetime) = date('now')
        """
    ).fetchone()
    return jsonify(count=row["count"])


@auth_bp.route("/admin/stats/appointments/no-shows", methods=["GET"])
@require_role("admin")
def admin_no_shows_count():
    db = get_db()
    row = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM appointments
        WHERE status = 'NO_SHOW'
        """
    ).fetchone()
    return jsonify(count=row["count"])


@auth_bp.route("/admin/appointments", methods=["GET"])
@require_role("admin")
def admin_view_appointments():
    db = get_db()
    rows = db.execute(
        """
        SELECT
            a.id AS appointment_id,
            a.patient_id,
            p.name AS patient_name,
            a.doctor_id,
            d.name AS doctor_name,
            a.start_datetime,
            a.end_datetime,
            a.status,
            substr(a.start_datetime, 1, 10) AS appt_date
        FROM appointments a
        JOIN patients p ON p.user_id = a.patient_id
        JOIN doctors d ON d.user_id = a.doctor_id
        ORDER BY a.start_datetime
        """
    ).fetchall()

    return jsonify([dict(row) for row in rows])

# =========================
# Doctor Availability (Non-Lifecycle)
# =========================

@auth_bp.route("/doctor/availability", methods=["POST"])
@require_role("doctor")
def create_availability():
    data = request.get_json(force=True)
    availability_date = data.get("date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    if not availability_date or not start_time or not end_time:
        return jsonify(error="Missing required fields"), 400

    db = get_db()
    db.execute(
        """
        INSERT INTO doctor_availability (doctor_id, date, start_time, end_time)
        VALUES (?, ?, ?, ?)
        """,
        (request.user_id, availability_date, start_time, end_time),
    )
    db.commit()

    return jsonify(
        message="Availability created",
        doctor_id=request.user_id,
        date=availability_date,
        start_time=start_time,
        end_time=end_time,
    ), 201


@auth_bp.route("/doctor/availability", methods=["GET"])
@require_role("doctor")
def get_doctor_availability():
    db = get_db()
    rows = db.execute(
        """
        SELECT id, date, start_time, end_time
        FROM doctor_availability
        WHERE doctor_id = ?
        ORDER BY date, start_time
        """,
        (request.user_id,),
    ).fetchall()

    return jsonify(
        [
            {
                "id": row["id"],
                "date": row["date"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
            }
            for row in rows
        ]
    )

