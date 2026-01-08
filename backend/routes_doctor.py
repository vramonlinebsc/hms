from flask import Blueprint, jsonify, request
from datetime import datetime

from backend.db import get_db
from backend.routes import require_role

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")
patient_bp = Blueprint("patient",__name__,url_prefix="/patient")

ALLOWED_STATUSES = {
    "BOOKED",
    "COMPLETED",
    "CANCELLED_BY_ADMIN",
    "CANCELLED_BY_DOCTOR",
    "NO_SHOW",
}


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


@doctor_bp.route("/patients/<int:patient_id>/history", methods=["GET"])
@require_role("doctor")
def view_patient_history(patient_id):
    doctor_id = request.user_id
    db = get_db()

    # Authorization guard:
    # doctor must have treated (or been assigned to) this patient at least once
    auth_row = db.execute(
        """
        SELECT 1
        FROM appointments
        WHERE doctor_id = ?
          AND patient_id = ?
        """,
        (doctor_id, patient_id)
    ).fetchone()

    if not auth_row:
        return jsonify(error="Unauthorized access to patient history"), 403

    rows = db.execute(
        """
        SELECT
            a.id AS appointment_id,
            a.start_datetime,
            a.end_datetime,
            a.status,
            a.diagnosis,
            a.treatment
        FROM appointments a
        WHERE a.patient_id = ?
          AND a.status IN ('COMPLETED', 'NO_SHOW')
        ORDER BY a.start_datetime DESC
        """,
        (patient_id,)
    ).fetchall()

    return jsonify([
        {
            "appointment_id": row["appointment_id"],
            "start_datetime": row["start_datetime"],
            "end_datetime": row["end_datetime"],
            "status": row["status"],
            "diagnosis": row["diagnosis"],
            "treatment": row["treatment"],
        }
        for row in rows
    ])


@patient_bp.route("/appointments", methods=["POST"])
@require_role("patient")
def create_appointment():
    patient_id = request.user_id
    data = request.get_json(force=True)

    doctor_id = data.get("doctor_id")
    start_datetime = data.get("start_datetime")
    end_datetime = data.get("end_datetime")

    if not doctor_id or not start_datetime or not end_datetime:
        return jsonify(error="doctor_id, start_datetime, end_datetime required"), 400

    try:
        start_dt = datetime.fromisoformat(start_datetime)
        end_dt = datetime.fromisoformat(end_datetime)
    except ValueError:
        return jsonify(error="Invalid datetime format"), 400

    if start_dt >= end_dt:
        return jsonify(error="Invalid time range"), 400

    if start_dt <= datetime.utcnow():
        return jsonify(error="Appointment must be in the future"), 400

    db = get_db()

    # Ensure doctor exists and is not blacklisted
    doctor = db.execute(
        """
        SELECT d.user_id
        FROM doctors d
        JOIN users u ON u.id = d.user_id
        WHERE d.user_id = ?
          AND u.is_active = 1
          AND d.is_blacklisted = 0
        """,
        (doctor_id,)
    ).fetchone()

    if not doctor:
        return jsonify(error="Doctor not available"), 400

    # Prevent overlapping appointments (doctor or patient)
    conflict = db.execute(
        """
        SELECT 1
        FROM appointments
        WHERE status = 'BOOKED'
          AND (
            doctor_id = ?
            OR patient_id = ?
          )
          AND NOT (
            end_datetime <= ?
            OR start_datetime >= ?
          )
        """,
        (doctor_id, patient_id, start_datetime, end_datetime)
    ).fetchone()

    if conflict:
        return jsonify(error="Appointment conflict detected"), 409

    cur = db.execute(
        """
        INSERT INTO appointments (
            doctor_id,
            patient_id,
            start_datetime,
            end_datetime,
            status
        )
        VALUES (?, ?, ?, ?, 'BOOKED')
        """,
        (doctor_id, patient_id, start_datetime, end_datetime)
    )

    appointment_id = cur.lastrowid

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
            "patient",
            patient_id,
            "appointment",
            appointment_id,
            "PATIENT_BOOKED_APPOINTMENT",
        )
    )

    db.commit()

    return jsonify(
        message="Appointment booked",
        appointment_id=appointment_id
    ), 201
