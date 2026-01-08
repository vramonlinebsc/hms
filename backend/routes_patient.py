from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import get_db
from backend.routes import require_role
from datetime import datetime

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

# =========================
# REGISTER
# =========================
@patient_bp.route("/register", methods=["POST"])
def register_patient():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify(error="Username and password required"), 400

    db = get_db()

    try:
        cur = db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'patient')",
            (username, generate_password_hash(password))
        )
        user_id = cur.lastrowid

        # 🔑 CRITICAL FIX: insert into patients table
        db.execute(
            "INSERT INTO patients (user_id, name) VALUES (?, ?)",
            (user_id, username)
        )

        db.commit()

    except Exception:
        return jsonify(error="Username already exists"), 400

    return jsonify(message="Patient registered successfully"), 201


# =========================
# LOGIN
# =========================
@patient_bp.route("/login", methods=["POST"])
def login_patient():
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
        (username,)
    ).fetchone()

    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    from backend.routes import make_token
    token = make_token(row["id"], "patient")

    return jsonify(
        patient_id=row["id"],
        token=token,
        message="Patient login successful"
    )


# =========================
# LIST APPOINTMENTS
# =========================
@patient_bp.route("/appointments", methods=["GET"])
@require_role("patient")
def list_patient_appointments():
    db = get_db()
    rows = db.execute(
        """
        SELECT
            a.id AS appointment_id,
            a.doctor_id,
            d.name AS doctor_name,
            a.start_datetime,
            a.end_datetime,
            a.status
        FROM appointments a
        JOIN doctors d ON d.user_id = a.doctor_id
        WHERE a.patient_id = ?
        ORDER BY a.start_datetime
        """,
        (request.user_id,)
    ).fetchall()

    return jsonify([dict(row) for row in rows])


# =========================
# BOOK APPOINTMENT
# =========================
@patient_bp.route("/appointments", methods=["POST"])
@require_role("patient")
def book_appointment():
    data = request.get_json() or {}
    doctor_id = data.get("doctor_id")
    start = data.get("start_datetime")
    end = data.get("end_datetime")

    if not doctor_id or not start or not end:
        return jsonify(error="Missing required fields"), 400

    start_dt = datetime.fromisoformat(start)
    if start_dt <= datetime.utcnow():
        return jsonify(error="Appointment must be in the future"), 400

    db = get_db()

    try:
        db.execute(
            """
            INSERT INTO appointments
            (patient_id, doctor_id, start_datetime, end_datetime)
            VALUES (?, ?, ?, ?)
            """,
            (request.user_id, doctor_id, start, end)
        )
        db.commit()
    except Exception:
        return jsonify(error="Appointment slot unavailable"), 409

    return jsonify(message="Appointment booked"), 201


# =========================
# CANCEL APPOINTMENT
# =========================
@patient_bp.route("/appointments/<int:appointment_id>/cancel", methods=["PATCH"])
@require_role("patient")
def cancel_patient_appointment(appointment_id):
    db = get_db()

    appt = db.execute(
        """
        SELECT id, start_datetime, status
        FROM appointments
        WHERE id = ?
          AND patient_id = ?
        """,
        (appointment_id, request.user_id)
    ).fetchone()

    if not appt:
        return jsonify(error="Appointment not found"), 404

    if appt["status"] != "BOOKED":
        return jsonify(error="Appointment cannot be cancelled"), 409

    start_dt = datetime.fromisoformat(appt["start_datetime"])
    if datetime.utcnow() >= start_dt:
        return jsonify(error="Too late to cancel appointment"), 409

    db.execute(
        """
        UPDATE appointments
        SET status = 'CANCELLED_BY_PATIENT'
        WHERE id = ?
        """,
        (appointment_id,)
    )
    db.commit()

    return jsonify(
    message="Appointment cancelled",
    status="CANCELLED_BY_PATIENT"
    )

