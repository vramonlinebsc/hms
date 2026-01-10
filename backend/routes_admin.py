from flask import Blueprint, jsonify, request
from backend.db import get_db
from backend.routes import require_role

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/appointments", methods=["GET"])
@require_role("admin")
def list_appointments():
    db = get_db()

    rows = db.execute(
        """
        SELECT
            a.id            AS appointment_id,
            a.status        AS status,
            s.slot_time     AS start_datetime,

            pu.id           AS patient_id,
            pu.username     AS patient_name,

            du.id           AS doctor_id,
            du.username     AS doctor_name

        FROM appointments a
        JOIN doctor_slots s ON s.id = a.slot_id
        JOIN users pu ON pu.id = a.patient_id
        JOIN users du ON du.id = s.doctor_id

        ORDER BY s.slot_time ASC, a.id ASC
        """
    ).fetchall()

    return jsonify([
        {
            "appointment_id": r["appointment_id"],
            "status": r["status"],
            "start_datetime": r["start_datetime"],
            "patient": {
                "id": r["patient_id"],
                "username": r["patient_name"],
            },
            "doctor": {
                "id": r["doctor_id"],
                "username": r["doctor_name"],
            },
        }
        for r in rows
    ]), 200


@admin_bp.route("/appointments/<int:appointment_id>/cancel", methods=["PATCH"])
@require_role("admin")
def cancel_appointment(appointment_id):
    db = get_db()

    row = db.execute(
        """
        SELECT id, status
        FROM appointments
        WHERE id = ?
        """,
        (appointment_id,)
    ).fetchone()

    if not row:
        return jsonify(error="Appointment not found"), 404

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
        VALUES (?, 'admin', ?, 'CANCELLED_BY_ADMIN')
        """,
        (appointment_id, request.user_id)
    )

    db.commit()

    return jsonify(
        message="Appointment cancelled",
        status="CANCELLED_BY_ADMIN"
    ), 200
