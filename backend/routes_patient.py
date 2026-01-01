# backend/routes_patient.py

from flask import Blueprint, jsonify, request
from backend.db import get_db
from backend.routes import require_role
from datetime import datetime

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

ALLOWED_STATUSES = {
    "BOOKED",
    "COMPLETED",
    "CANCELLED_BY_ADMIN",
    "CANCELLED_BY_DOCTOR",
    "NO_SHOW",
}

@patient_bp.route("/appointments", methods=["GET"])
@require_role("patient")
def list_patient_appointments():
    patient_id = request.user_id

    date = request.args.get("date")
    status = request.args.get("status")

    if status and status not in ALLOWED_STATUSES:
        return jsonify(error="Invalid status filter"), 400

    db = get_db()

    query = """
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
    """
    params = [patient_id]

    if date:
        query += " AND date(a.start_datetime) = ?"
        params.append(date)

    if status:
        query += " AND a.status = ?"
        params.append(status)

    query += " ORDER BY a.start_datetime ASC"

    rows = db.execute(query, params).fetchall()

    return jsonify([
        {
            "appointment_id": row["appointment_id"],
            "doctor_id": row["doctor_id"],
            "doctor_name": row["doctor_name"],
            "start_datetime": row["start_datetime"],
            "end_datetime": row["end_datetime"],
            "status": row["status"],
        }
        for row in rows
    ])


@patient_bp.route("/appointments", methods=["POST"])
@require_role("patient")
def book_appointment():
    data = request.get_json() or {}

    doctor_id = data.get("doctor_id")
    start_dt = data.get("start_datetime")
    end_dt = data.get("end_datetime")

    if not doctor_id or not start_dt or not end_dt:
        return jsonify(error="Missing required fields"), 400

    try:
        start_dt_parsed = datetime.fromisoformat(start_dt)
        end_dt_parsed = datetime.fromisoformat(end_dt)
    except ValueError:
        return jsonify(error="Invalid datetime format"), 400

    if start_dt_parsed >= end_dt_parsed:
        return jsonify(error="Invalid time range"), 400

    if start_dt_parsed <= datetime.utcnow():
        return jsonify(error="Appointment must be in the future"), 409

    db = get_db()

    doctor = db.execute(
        """
        SELECT 1
        FROM doctors d
        JOIN users u ON u.id = d.user_id
        WHERE d.user_id = ?
          AND u.is_active = 1
        """,
        (doctor_id,)
    ).fetchone()

    if not doctor:
        return jsonify(error="Doctor not available"), 404

    conflict = db.execute(
        """
        SELECT 1
        FROM appointments
        WHERE doctor_id = ?
          AND status = 'BOOKED'
          AND (? < end_datetime AND ? > start_datetime)
        """,
        (doctor_id, start_dt, end_dt)
    ).fetchone()

    if conflict:
        return jsonify(error="Slot already booked"), 409

    try:
        db.execute(
            """
            INSERT INTO appointments (
                patient_id,
                doctor_id,
                start_datetime,
                end_datetime,
                status
            )
            VALUES (?, ?, ?, ?, 'BOOKED')
            """,
            (request.user_id, doctor_id, start_dt, end_dt)
        )
        db.commit()
    except Exception:
        return jsonify(error="Duplicate or invalid booking"), 409

    return jsonify(
        message="Appointment booked",
        doctor_id=doctor_id,
        start_datetime=start_dt,
        end_datetime=end_dt,
        status="BOOKED"
    ), 201


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
        SET status = 'CANCELLED_BY_ADMIN'
        WHERE id = ?
        """,
        (appointment_id,)
    )

    db.execute(
        """
        INSERT INTO audit_logs (
            actor_role,
            actor_id,
            action,
            appointment_id
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            "patient",
            request.user_id,
            "PATIENT_CANCELLED_APPOINTMENT",
            appointment_id,
        )
    )

    db.commit()

    return jsonify(
        message="Appointment cancelled",
        appointment_id=appointment_id,
        status="CANCELLED_BY_ADMIN"
    )

