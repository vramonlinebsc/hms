from flask import Blueprint, jsonify, request
from datetime import datetime

from backend.db import get_db
from backend.routes import require_role

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")

ALLOWED_STATUSES = {
    "BOOKED",
    "COMPLETED",
    "CANCELLED_BY_ADMIN",
    "CANCELLED_BY_DOCTOR",
    "NO_SHOW",
}

# --------------------------------------------------
# B1.1 — List Doctor Appointments (Read-only)
# --------------------------------------------------
@doctor_bp.route("/appointments", methods=["GET"])
@require_role("doctor")
def list_doctor_appointments():
    doctor_id = request.user_id

    date = request.args.get("date")
    status = request.args.get("status")

    if status and status not in ALLOWED_STATUSES:
        return jsonify(error="Invalid status filter"), 400

    db = get_db()

    query = """
        SELECT
            a.id AS appointment_id,
            a.patient_id,
            u.username AS patient_username,
            a.start_datetime,
            a.end_datetime,
            a.status
        FROM appointments a
        JOIN users u ON u.id = a.patient_id
        WHERE a.doctor_id = ?
    """
    params = [doctor_id]

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
            "patient_id": row["patient_id"],
            "patient_username": row["patient_username"],
            "start_datetime": row["start_datetime"],
            "end_datetime": row["end_datetime"],
            "status": row["status"],
        }
        for row in rows
    ])


# --------------------------------------------------
# B1.2 — Doctor Marks Appointment as COMPLETED
# --------------------------------------------------
@doctor_bp.route("/appointments/<int:appointment_id>/complete", methods=["PATCH"])
@require_role("doctor")
def complete_appointment(appointment_id):
    doctor_id = request.user_id
    db = get_db()

    row = db.execute(
        """
        SELECT id, status, end_datetime
        FROM appointments
        WHERE id = ?
          AND doctor_id = ?
        """,
        (appointment_id, doctor_id)
    ).fetchone()

    if not row:
        return jsonify(error="Appointment not found"), 404

    if row["status"] == "COMPLETED":
        return jsonify(message="Appointment already completed"), 200

    if row["status"] != "BOOKED":
        return jsonify(error="Invalid state transition"), 409

    now = datetime.utcnow()
    end_dt = datetime.fromisoformat(row["end_datetime"])

    if now < end_dt:
        return jsonify(error="Cannot complete before appointment ends"), 409

    db.execute(
        "UPDATE appointments SET status = 'COMPLETED' WHERE id = ?",
        (appointment_id,)
    )

    db.execute(
        """
        INSERT INTO audit_logs (
            actor_role,
            actor_id,
            entity_type,
            entity_id,
            action
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "doctor",
            doctor_id,
            "appointment",
            appointment_id,
            "DOCTOR_COMPLETED_APPOINTMENT",
        )
    )

    db.commit()

    return jsonify(
        message="Appointment marked as completed",
        appointment_id=appointment_id
    ), 200


# --------------------------------------------------
# B1.3 — Doctor Cancels Appointment (Pre-start Only)
# --------------------------------------------------
@doctor_bp.route("/appointments/<int:appointment_id>/cancel", methods=["PATCH"])
@require_role("doctor")
def cancel_appointment_by_doctor(appointment_id):
    doctor_id = request.user_id
    db = get_db()

    row = db.execute(
        """
        SELECT id, status, start_datetime
        FROM appointments
        WHERE id = ?
          AND doctor_id = ?
        """,
        (appointment_id, doctor_id)
    ).fetchone()

    if not row:
        return jsonify(error="Appointment not found"), 404

    if row["status"] == "CANCELLED_BY_DOCTOR":
        return jsonify(message="Appointment already cancelled"), 200

    if row["status"] != "BOOKED":
        return jsonify(error="Invalid state transition"), 409

    now = datetime.utcnow()
    start_dt = datetime.fromisoformat(row["start_datetime"])

    if now >= start_dt:
        return jsonify(error="Cannot cancel after appointment start time"), 409

    db.execute(
        "UPDATE appointments SET status = 'CANCELLED_BY_DOCTOR' WHERE id = ?",
        (appointment_id,)
    )

    db.execute(
        """
        INSERT INTO audit_logs (
            actor_role,
            actor_id,
            entity_type,
            entity_id,
            action
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "doctor",
            doctor_id,
            "appointment",
            appointment_id,
            "DOCTOR_CANCELLED_APPOINTMENT",
        )
    )

    db.commit()

    return jsonify(
        message="Appointment cancelled by doctor",
        appointment_id=appointment_id
    ), 200

