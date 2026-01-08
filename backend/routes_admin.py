# backend/routes_admin.py

from flask import Blueprint, jsonify, request
from datetime import datetime
from backend.db import get_db
from backend.routes import require_role

# -------------------------------------------------------------------
# Canonical admin blueprint
# -------------------------------------------------------------------

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# -------------------------------------------------------------------
# A1 — ADMIN READ-ONLY APPOINTMENT LIST
# -------------------------------------------------------------------

@admin_bp.route("/appointments", methods=["GET"])
@require_role("admin")
def list_appointments():
    """
    Admin-only, read-only appointment listing.
    Deterministic ordering.
    Optional filters:
      - date (YYYY-MM-DD, derived from start_datetime)
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
        filters.append("date(a.start_datetime) = ?")
        params.append(appt_date)

    if doctor_id:
        filters.append("a.doctor_id = ?")
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
            a.id             AS appointment_id,
            a.start_datetime AS start_datetime,
            a.end_datetime   AS end_datetime,
            a.status         AS status,

            pu.id            AS patient_id,
            pu.username      AS patient_name,

            du.id            AS doctor_id,
            du.username      AS doctor_name

        FROM appointments a
        JOIN users pu ON pu.id = a.patient_id
        JOIN users du ON du.id = a.doctor_id

        {where_clause}

        ORDER BY
            a.start_datetime ASC,
            a.id ASC
        """,
        params
    ).fetchall()

    return jsonify([
        {
            "appointment_id": row["appointment_id"],
            "start_datetime": row["start_datetime"],
            "end_datetime": row["end_datetime"],
            "status": row["status"],
            "patient_id": row["patient_id"],
            "patient_name": row["patient_name"],
            "doctor_id": row["doctor_id"],
            "doctor_name": row["doctor_name"],
        }
        for row in rows
    ])


# -------------------------------------------------------------------
# A2 — ADMIN CANCEL APPOINTMENT
# -------------------------------------------------------------------

ALLOWED_CANCEL_STATES = {"BOOKED"}


@admin_bp.route("/appointments/<int:appointment_id>/cancel", methods=["PATCH"])
@require_role("admin")
def cancel_appointment(appointment_id):
    """
    Admin-only cancellation.
    Enforces lifecycle integrity.
    Idempotent.
    """

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

    current_status = row["status"]

    # Idempotent replay
    if current_status == "CANCELLED_BY_ADMIN":
        return jsonify(
            appointment_id=appointment_id,
            status=current_status,
            message="Appointment already cancelled by admin"
        ), 200

    # Illegal transition
    if current_status not in ALLOWED_CANCEL_STATES:
        return jsonify(
            error="Illegal state transition",
            from_status=current_status,
            to_status="CANCELLED_BY_ADMIN"
        ), 409

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
            entity_type,
            entity_id,
            action,
            actor_role,
            actor_id
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "appointment",
            appointment_id,
            "CANCELLED_BY_ADMIN",
            "admin",
            request.user_id,
        )
    )

    db.commit()

    return jsonify(
        appointment_id=appointment_id,
        previous_status=current_status,
        status="CANCELLED_BY_ADMIN",
        message="Appointment cancelled by admin"
    ), 200


# -------------------------------------------------------------------
# A3 — ADMIN CONFIRM NO-SHOW
# -------------------------------------------------------------------

ALLOWED_NO_SHOW_STATES = {"BOOKED"}


@admin_bp.route(
    "/appointments/<int:appointment_id>/confirm-no-show",
    methods=["PATCH"]
)
@require_role("admin")
def confirm_no_show(appointment_id):
    """
    Admin-only NO_SHOW confirmation.
    Enforces time and state invariants.
    Idempotent.
    """

    db = get_db()

    row = db.execute(
        """
        SELECT id, status, end_datetime
        FROM appointments
        WHERE id = ?
        """,
        (appointment_id,)
    ).fetchone()

    if not row:
        return jsonify(error="Appointment not found"), 404

    current_status = row["status"]

    try:
        end_dt = datetime.fromisoformat(row["end_datetime"])
    except Exception:
        return jsonify(error="Invalid appointment end_datetime format"), 500

    now = datetime.utcnow()

    if now <= end_dt:
        return jsonify(
            error="Cannot mark NO_SHOW before appointment end time",
            now=now.isoformat(),
            end_datetime=end_dt.isoformat()
        ), 409

    # Idempotent replay
    if current_status == "NO_SHOW":
        return jsonify(
            appointment_id=appointment_id,
            status="NO_SHOW",
            message="Appointment already marked as NO_SHOW"
        ), 200

    # Illegal transition
    if current_status not in ALLOWED_NO_SHOW_STATES:
        return jsonify(
            error="Illegal state transition",
            from_status=current_status,
            to_status="NO_SHOW"
        ), 409

    db.execute(
        """
        UPDATE appointments
        SET status = 'NO_SHOW'
        WHERE id = ?
        """,
        (appointment_id,)
    )

    db.execute(
        """
        INSERT INTO audit_logs (
            entity_type,
            entity_id,
            action,
            actor_role,
            actor_id
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "appointment",
            appointment_id,
            "NO_SHOW_CONFIRMED",
            "admin",
            request.user_id,
        )
    )

    db.commit()

    return jsonify(
        appointment_id=appointment_id,
        previous_status=current_status,
        status="NO_SHOW",
        message="Appointment marked as NO_SHOW by admin"
    ), 200


# -------------------------------------------------------------------
# A4 — ADMIN READ-ONLY NO-SHOW LIST
# -------------------------------------------------------------------

@admin_bp.route("/no-shows", methods=["GET"])
@require_role("admin")
def get_no_show_appointments():
    """
    Admin-only, read-only list of NO_SHOW appointments.
    """

    db = get_db()

    rows = db.execute(
        """
        SELECT
            id AS appointment_id,
            patient_id,
            doctor_id,
            start_datetime,
            end_datetime,
            status
        FROM appointments
        WHERE status = 'NO_SHOW'
        ORDER BY end_datetime DESC
        """
    ).fetchall()

    return jsonify([
        {
            "appointment_id": row["appointment_id"],
            "patient_id": row["patient_id"],
            "doctor_id": row["doctor_id"],
            "start_datetime": row["start_datetime"],
            "end_datetime": row["end_datetime"],
            "status": row["status"]
        }
        for row in rows
    ])

