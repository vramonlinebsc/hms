from flask import Blueprint, jsonify, request
from datetime import datetime

from backend.db import get_db
from backend.routes import require_role

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# =====================================================
# LIST APPOINTMENTS (SLOT-BASED)
# =====================================================
@admin_bp.route("/appointments", methods=["GET"])
@require_role("admin")
def list_appointments():
    """
    Admin-only, read-only appointment listing.
    Optional filters:
      - date (YYYY-MM-DD, derived from slot start_datetime)
      - doctor_id
      - status
    """

    db = get_db()

    filters = []
    params = []

    appt_date = request.args.get("date")
    doctor_id = request.args.get("doctor_id")
    status = request.args.get("status")

    if appt_date:
        filters.append("date(s.start_datetime) = ?")
        params.append(appt_date)

    if doctor_id:
        filters.append("s.doctor_id = ?")
        params.append(doctor_id)

    if status:
        filters.append("a.status = ?")
        params.append(status)

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    rows = db.execute(
        f"""
        SELECT
            a.id              AS appointment_id,
            a.status          AS status,
            s.start_datetime  AS start_datetime,
            s.end_datetime    AS end_datetime,

            pu.id             AS patient_id,
            pu.username       AS patient_name,

            du.id             AS doctor_id,
            du.username       AS doctor_name

        FROM appointments a
        JOIN doctor_slots s ON s.id = a.slot_id
        JOIN users pu ON pu.id = a.patient_id
        JOIN users du ON du.id = s.doctor_id

        {where_clause}

        ORDER BY
            s.start_datetime ASC,
            a.id ASC
        """,
        params
    ).fetchall()

    return jsonify([dict(row) for row in rows])


# =====================================================
# CANCEL APPOINTMENT (ADMIN)
# =====================================================
@admin_bp.route("/appointments/<int:appointment_id>/cancel", methods=["PATCH"])
@require_role("admin")
def cancel_appointment_by_admin(appointment_id):
    db = get_db()

    row = db.execute(
        """
        SELECT a.status
        FROM appointments a
        WHERE a.id = ?
        """,
        (appointment_id,)
    ).fetchone()

    if not row:
        return jsonify(error="Appointment not found"), 404

    if row["status"] != "BOOKED":
        return jsonify(error="Appointment cannot be cancelled"), 409

    db.execute(
        """
        UPDATE appointments
        SET status = 'CANCELLED_BY_ADMIN'
        WHERE id = ?
        """,
        (appointment_id,)
    )
    db.commit()

    return jsonify(
        message="Appointment cancelled by admin",
        status="CANCELLED_BY_ADMIN"
    )
