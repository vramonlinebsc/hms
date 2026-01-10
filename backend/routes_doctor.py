from flask import Blueprint, jsonify, request
from backend.db import get_db
from backend.routes import require_role

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")


@doctor_bp.route("/slots", methods=["POST"])
@require_role("doctor")
def create_slot():
    data = request.get_json() or {}

    start = data.get("start_datetime")
    end = data.get("end_datetime")

    if not start or not end:
        return jsonify(error="start_datetime and end_datetime required"), 400

    db = get_db()
    cur = db.execute(
        """
        INSERT INTO doctor_slots (doctor_id, slot_time, is_booked)
        VALUES (?, ?, 0)
        """,
        (request.user_id, start)
    )
    db.commit()

    return jsonify(
        slot_id=cur.lastrowid,
        doctor_id=request.user_id,
        start_datetime=start,
        end_datetime=end
    ), 201


@doctor_bp.route("/appointments/<int:appointment_id>/complete", methods=["POST"])
@require_role("doctor")
def complete_appointment(appointment_id):
    db = get_db()

    row = db.execute(
        """
        SELECT a.id, a.status, s.doctor_id
        FROM appointments a
        JOIN doctor_slots s ON s.id = a.slot_id
        WHERE a.id = ?
        """,
        (appointment_id,)
    ).fetchone()

    if not row:
        return jsonify(error="Appointment not found"), 404

    if row["doctor_id"] != int(request.user_id):
        return jsonify(error="Forbidden"), 403

    if row["status"] != "booked":
        return jsonify(error="Only booked appointments can be completed"), 400

    # update appointment
    db.execute(
        "UPDATE appointments SET status = 'completed' WHERE id = ?",
        (appointment_id,)
    )

    # audit log
    db.execute(
        """
        INSERT INTO appointment_audit_logs
        (appointment_id, actor_role, actor_id, action)
        VALUES (?, 'doctor', ?, 'COMPLETED')
        """,
        (appointment_id, request.user_id)
    )

    db.commit()

    return jsonify(
        appointment_id=appointment_id,
        status="COMPLETED"
    )


@doctor_bp.route("/appointments/<int:appointment_id>/no-show", methods=["POST"])
@require_role("doctor")
def mark_no_show(appointment_id):
    db = get_db()

    row = db.execute(
        """
        SELECT a.id, a.status, s.doctor_id
        FROM appointments a
        JOIN doctor_slots s ON s.id = a.slot_id
        WHERE a.id = ?
        """,
        (appointment_id,)
    ).fetchone()

    if not row:
        return jsonify(error="Appointment not found"), 404

    if row["doctor_id"] != int(request.user_id):
        return jsonify(error="Forbidden"), 403

    if row["status"] != "booked":
        return jsonify(error="Only booked appointments can be marked no-show"), 400

    # update appointment
    db.execute(
        "UPDATE appointments SET status = 'no_show' WHERE id = ?",
        (appointment_id,)
    )

    # audit log
    db.execute(
        """
        INSERT INTO appointment_audit_logs
        (appointment_id, actor_role, actor_id, action)
        VALUES (?, 'doctor', ?, 'NO_SHOW')
        """,
        (appointment_id, request.user_id)
    )

    db.commit()

    return jsonify(
        appointment_id=appointment_id,
        status="NO_SHOW"
    )
