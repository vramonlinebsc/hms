from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import get_db
from backend.routes import require_role
from backend.config import SECRET_KEY, JWT_ALGO, JWT_EXP_SECONDS
from datetime import datetime, timedelta
import jwt

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")


@patient_bp.route("/register", methods=["POST"])
def register_patient():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify(error="Username and password required"), 400

    db = get_db()

    existing = db.execute(
        "SELECT id FROM users WHERE username=?",
        (username,)
    ).fetchone()

    if existing:
        return jsonify(error="Username already exists"), 400

    password_hash = generate_password_hash(password)

    db.execute(
        """
        INSERT INTO users (username, password_hash, role, is_active)
        VALUES (?, ?, 'patient', 1)
        """,
        (username, password_hash)
    )
    db.commit()

    return jsonify(message="Patient registered successfully"), 201


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

    payload = {
        "sub": str(row["id"]),
        "role": "patient",
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_SECONDS)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGO)

    return jsonify(
        patient_id=row["id"],
        token=token,
        message="Patient login successful"
    )


@patient_bp.route("/appointments", methods=["POST"])
@require_role("patient")
def book_appointment():
    data = request.get_json(force=True)

    slot_id = data.get("slot_id")
    doctor_id = data.get("doctor_id")
    start = data.get("start_datetime")

    db = get_db()

    # --------------------------------------
    # SLOT-BASED PATH (preferred)
    # --------------------------------------
    if slot_id:
        slot = db.execute(
            """
            SELECT id, doctor_id, is_booked
            FROM doctor_slots
            WHERE id = ?
            """,
            (slot_id,)
        ).fetchone()

        if not slot:
            return jsonify(error="Slot not found"), 404

        if slot["is_booked"]:
            return jsonify(error="Slot already booked"), 409

        db.execute(
            "UPDATE doctor_slots SET is_booked = 1 WHERE id = ?",
            (slot_id,)
        )

        db.execute(
            """
            INSERT INTO appointments (patient_id, slot_id, status)
            VALUES (?, ?, 'booked')
            """,
            (request.user_id, slot_id)
        )

        db.commit()

        return jsonify(
            message="Appointment booked",
            slot_id=slot_id
        ), 201

    # --------------------------------------
    # LEGACY DATETIME PATH (compatibility)
    # --------------------------------------
    if not doctor_id or not start:
        return jsonify(error="Missing fields"), 400

    cur = db.execute(
        """
        INSERT INTO doctor_slots (doctor_id, slot_time, is_booked)
        VALUES (?, ?, 1)
        """,
        (doctor_id, start)
    )
    new_slot_id = cur.lastrowid

    db.execute(
        """
        INSERT INTO appointments (patient_id, slot_id, status)
        VALUES (?, ?, 'booked')
        """,
        (request.user_id, new_slot_id)
    )

    db.commit()

    return jsonify(
        message="Appointment booked",
        slot_id=new_slot_id
    ), 201


@patient_bp.route("/appointments", methods=["GET"])
@require_role("patient")
def list_patient_appointments():
    db = get_db()

    rows = db.execute(
        """
        SELECT
            a.id        AS appointment_id,
            a.status    AS status,
            s.slot_time AS start_datetime,
            u.username  AS doctor_name
        FROM appointments a
        JOIN doctor_slots s ON s.id = a.slot_id
        JOIN users u ON u.id = s.doctor_id
        WHERE a.patient_id = ?
        ORDER BY s.slot_time ASC
        """,
        (request.user_id,)
    ).fetchall()

    return jsonify([
        {
            "appointment_id": r["appointment_id"],
            "status": r["status"],
            "start_datetime": r["start_datetime"],
            "doctor": r["doctor_name"]
        }
        for r in rows
    ]), 200


@patient_bp.route("/appointments/<int:appointment_id>/cancel", methods=["PATCH"])
@require_role("patient")
def cancel_appointment_by_patient(appointment_id):
    db = get_db()

    row = db.execute(
        """
        SELECT id, patient_id, status
        FROM appointments
        WHERE id = ?
        """,
        (appointment_id,)
    ).fetchone()

    if not row:
        return jsonify(error="Appointment not found"), 404

    if row["patient_id"] != request.user_id:
        return jsonify(error="Forbidden"), 403

    # update appointment
    db.execute(
        "UPDATE appointments SET status = 'cancelled' WHERE id = ?",
        (appointment_id,)
    )

    # audit log
    db.execute(
        """
        INSERT INTO appointment_audit_logs
        (appointment_id, actor_role, actor_id, action)
        VALUES (?, 'patient', ?, 'CANCELLED_BY_PATIENT')
        """,
        (appointment_id, request.user_id)
    )

    db.commit()

    return jsonify(
        message="Appointment cancelled",
        status="CANCELLED_BY_PATIENT"
    ), 200
