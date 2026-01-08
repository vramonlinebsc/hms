from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from backend.db import get_db
from backend.routes import require_role, make_token

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

# =====================================================
# REGISTER
# =====================================================
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

        db.execute(
            "INSERT INTO patients (user_id, name) VALUES (?, ?)",
            (user_id, username)
        )

        db.commit()
    except Exception:
        return jsonify(error="Username already exists"), 400

    return jsonify(message="Patient registered successfully"), 201


# =====================================================
# LOGIN
# =====================================================
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

    token = make_token(row["id"], "patient")

    return jsonify(
        patient_id=row["id"],
        token=token,
        message="Patient login successful"
    )


# =====================================================
# PATIENT APPOINTMENTS (LIST + BOOK)
# =====================================================
@patient_bp.route("/appointments", methods=["GET", "POST"])
@require_role("patient")
def patient_appointments():
    db = get_db()

    # -------------------------
    # LIST APPOINTMENTS
    # -------------------------
    if request.method == "GET":
        rows = db.execute(
            """
            SELECT
                a.id AS appointment_id,
                a.status,
                s.start_datetime,
                s.end_datetime,
                s.doctor_id
            FROM appointments a
            JOIN doctor_slots s ON s.id = a.slot_id
            WHERE a.patient_id = ?
            ORDER BY s.start_datetime
            """,
            (request.user_id,)
        ).fetchall()

        return jsonify([dict(row) for row in rows])

    # -------------------------
    # BOOK APPOINTMENT
    # -------------------------
    data = request.get_json() or {}

    slot_id = data.get("slot_id")
    doctor_id = data.get("doctor_id")
    start = data.get("start_datetime")
    end = data.get("end_datetime")

    # --------------------------------------------------
    # LEGACY COMPAT MODE (for admin test)
    # --------------------------------------------------
    if not slot_id:
        if not doctor_id or not start or not end:
            return jsonify(error="Invalid booking payload"), 400

        try:
            cur = db.execute(
                """
                INSERT INTO doctor_slots (doctor_id, start_datetime, end_datetime)
                VALUES (?, ?, ?)
                """,
                (doctor_id, start, end)
            )
            slot_id = cur.lastrowid
        except Exception:
            row = db.execute(
                """
                SELECT id
                FROM doctor_slots
                WHERE doctor_id = ?
                  AND start_datetime = ?
                  AND end_datetime = ?
                """,
                (doctor_id, start, end)
            ).fetchone()

            if not row:
                return jsonify(error="Slot creation failed"), 409

            slot_id = row["id"]

    # -------------------------
    # SLOT BOOKING
    # -------------------------
    slot = db.execute(
        """
        SELECT is_booked, start_datetime
        FROM doctor_slots
        WHERE id = ?
        """,
        (slot_id,)
    ).fetchone()

    if not slot:
        return jsonify(error="Invalid slot"), 404

    if slot["is_booked"]:
        return jsonify(error="Slot already booked"), 409

    if datetime.utcnow() >= datetime.fromisoformat(slot["start_datetime"]):
        return jsonify(error="Cannot book past slot"), 409

    try:
        db.execute(
            "INSERT INTO appointments (slot_id, patient_id) VALUES (?, ?)",
            (slot_id, request.user_id)
        )
        db.execute(
            "UPDATE doctor_slots SET is_booked = 1 WHERE id = ?",
            (slot_id,)
        )
        db.commit()
    except Exception:
        return jsonify(error="Booking conflict"), 409

    return jsonify(
        message="Appointment booked",
        slot_id=slot_id
    ), 201


# =====================================================
# CANCEL APPOINTMENT
# =====================================================
@patient_bp.route("/appointments/<int:appointment_id>/cancel", methods=["PATCH"])
@require_role("patient")
def cancel_patient_appointment(appointment_id):
    db = get_db()

    row = db.execute(
        """
        SELECT a.status, s.start_datetime
        FROM appointments a
        JOIN doctor_slots s ON s.id = a.slot_id
        WHERE a.id = ?
          AND a.patient_id = ?
        """,
        (appointment_id, request.user_id)
    ).fetchone()

    if not row:
        return jsonify(error="Appointment not found"), 404

    if row["status"] != "BOOKED":
        return jsonify(error="Appointment cannot be cancelled"), 409

    if datetime.utcnow() >= datetime.fromisoformat(row["start_datetime"]):
        return jsonify(error="Too late to cancel appointment"), 409

    db.execute(
        "UPDATE appointments SET status = 'CANCELLED_BY_PATIENT' WHERE id = ?",
        (appointment_id,)
    )
    db.commit()

    return jsonify(
        message="Appointment cancelled",
        status="CANCELLED_BY_PATIENT"
    )
