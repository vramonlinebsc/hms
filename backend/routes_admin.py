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



@admin_bp.route("/stats", methods=["GET"])
@require_role("admin")
def admin_stats():
    db = get_db()

    total_doctors = db.execute(
        "SELECT COUNT(*) FROM doctors"
    ).fetchone()[0]

    active_doctors = db.execute(
        "SELECT COUNT(*) FROM doctors WHERE is_blacklisted = 0"
    ).fetchone()[0]

    total_patients = db.execute(
        "SELECT COUNT(*) FROM users WHERE role = 'patient'"
    ).fetchone()[0]

    total_appointments = db.execute(
        "SELECT COUNT(*) FROM appointments"
    ).fetchone()[0]

    active_appointments = db.execute(
        "SELECT COUNT(*) FROM appointments WHERE status = 'BOOKED'"
    ).fetchone()[0]

    cancelled_appointments = db.execute(
        "SELECT COUNT(*) FROM appointments WHERE status LIKE 'CANCEL%'"
    ).fetchone()[0]

    return jsonify({
        "total_doctors": total_doctors,
        "active_doctors": active_doctors,
        "total_patients": total_patients,
        "total_appointments": total_appointments,
        "active_appointments": active_appointments,
        "cancelled_appointments": cancelled_appointments
    }), 200


@admin_bp.route("/patients", methods=["GET"])
@require_role("admin")
def list_patients():
    db = get_db()
    rows = db.execute(
        """
        SELECT
            id,
            username,
            is_active,
            created_at
        FROM users
        WHERE role = 'patient'
        ORDER BY created_at DESC
        """
    ).fetchall()

    return jsonify([
        {
            "id": row["id"],
            "username": row["username"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ])


@admin_bp.route("/patients/<int:patient_id>/deactivate", methods=["PATCH"])
@require_role("admin")
def deactivate_patient(patient_id):
    db = get_db()
    cur = db.execute(
        "UPDATE users SET is_active = 0 WHERE id = ? AND role = 'patient'",
        (patient_id,),
    )

    if cur.rowcount == 0:
        return jsonify(error="Patient not found"), 404

    db.commit()
    return jsonify(message="Patient deactivated")


@admin_bp.route("/patients/<int:patient_id>/activate", methods=["PATCH"])
@require_role("admin")
def activate_patient(patient_id):
    db = get_db()
    cur = db.execute(
        "UPDATE users SET is_active = 1 WHERE id = ? AND role = 'patient'",
        (patient_id,),
    )

    if cur.rowcount == 0:
        return jsonify(error="Patient not found"), 404

    db.commit()
    return jsonify(message="Patient activated")