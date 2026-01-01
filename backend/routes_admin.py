from flask import Blueprint, jsonify, request
from backend.db import get_db
from backend.routes import require_role

# Canonical admin blueprint
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
    Optional filters via query params:
      - date (YYYY-MM-DD)
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
        filters.append("a.appt_date = ?")
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
            a.appt_date      AS appt_date,
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
            a.appt_date ASC,
            a.start_datetime ASC,
            a.id ASC
        """,
        params
    ).fetchall()

    return jsonify([
        {
            "appointment_id": row["appointment_id"],
            "appt_date": row["appt_date"],
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

ALLOWED_CANCEL_STATES = {"BOOKED", "CONFIRMED"}


@admin_bp.route("/appointments/<int:appointment_id>/cancel", methods=["PATCH"])
@require_role("admin")
def cancel_appointment(appointment_id):
    """
    Admin-only explicit cancellation.
    Idempotent.
    Enforces valid state transitions.
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

    # Append-only audit log
    db.execute(
        """
        INSERT INTO audit_logs (entity_type, entity_id, action)
        VALUES ('appointment', ?, 'CANCELLED_BY_ADMIN')
        """,
        (appointment_id,)
    )

    db.commit()

    return jsonify(
        appointment_id=appointment_id,
        previous_status=current_status,
        status="CANCELLED_BY_ADMIN",
        message="Appointment cancelled by admin"
    ), 200


# -------------------------------------------------------------------
# ADMIN READ-ONLY: NO-SHOWS
# -------------------------------------------------------------------

@admin_bp.route("/no-shows", methods=["GET"])
@require_role("admin")
def get_no_show_appointments():
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


# -------------------------------------------------------------------
# ADMIN READ-ONLY: NO-SHOW PENALTIES
# -------------------------------------------------------------------

@admin_bp.route("/penalties/no-shows", methods=["GET"])
@require_role("admin")
def admin_no_show_penalties():
    db = get_db()

    rows = db.execute(
        """
        SELECT
            id,
            patient_id,
            appointment_id,
            created_at
        FROM patient_no_show_penalties
        ORDER BY created_at DESC
        """
    ).fetchall()

    return jsonify([
        {
            "penalty_id": row["id"],
            "patient_id": row["patient_id"],
            "appointment_id": row["appointment_id"],
            "created_at": row["created_at"],
        }
        for row in rows
    ])
from datetime import datetime

ALLOWED_NO_SHOW_STATES = {"BOOKED", "CONFIRMED"}


@admin_bp.route(
    "/appointments/<int:appointment_id>/confirm-no-show",
    methods=["PATCH"]
)
@require_role("admin")
def confirm_no_show(appointment_id):
    """
    Admin-only explicit NO_SHOW confirmation.
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
    end_dt_raw = row["end_datetime"]

    # Parse end time (ISO-like stored string)
    try:
        end_dt = datetime.fromisoformat(end_dt_raw)
    except Exception:
        return jsonify(
            error="Invalid appointment end_datetime format"
        ), 500

    now = datetime.utcnow()

    # Temporal invariant
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

    # Perform transition
    db.execute(
        """
        UPDATE appointments
        SET status = 'NO_SHOW'
        WHERE id = ?
        """,
        (appointment_id,)
    )

    # Append-only audit log
    db.execute(
        """
        INSERT INTO audit_logs (entity_type, entity_id, action)
        VALUES ('appointment', ?, 'NO_SHOW_CONFIRMED')
        """,
        (appointment_id,)
    )

    db.commit()

    return jsonify(
        appointment_id=appointment_id,
        previous_status=current_status,
        status="NO_SHOW",
        message="Appointment marked as NO_SHOW by admin"
    ), 200
@admin_bp.route("/audit-logs", methods=["GET"])
@require_role("admin")
def get_audit_logs():
    """
    Admin-only, read-only audit log view.
    Deterministic ordering.
    Optional filters:
      - entity_type
      - entity_id
      - action
    """

    db = get_db()

    filters = []
    params = []

    entity_type = request.args.get("entity_type")
    entity_id = request.args.get("entity_id")
    action = request.args.get("action")

    if entity_type:
        filters.append("entity_type = ?")
        params.append(entity_type)

    if entity_id:
        filters.append("entity_id = ?")
        params.append(entity_id)

    if action:
        filters.append("action = ?")
        params.append(action)

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    rows = db.execute(
        f"""
        SELECT
            id,
            entity_type,
            entity_id,
            action,
            created_at
        FROM audit_logs
        {where_clause}
        ORDER BY created_at DESC, id DESC
        """,
        params
    ).fetchall()

    return jsonify([
        {
            "audit_id": row["id"],
            "entity_type": row["entity_type"],
            "entity_id": row["entity_id"],
            "action": row["action"],
            "created_at": row["created_at"],
        }
        for row in rows
    ])

