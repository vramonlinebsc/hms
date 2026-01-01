from flask import Blueprint, jsonify
from backend.db import get_db
from backend.routes import require_role

metrics_bp = Blueprint("metrics", __name__, url_prefix="/admin/metrics")


@metrics_bp.route("/no-shows", methods=["GET"])
@require_role("admin")
def no_show_counts():
    """
    Aggregate count of NO_SHOW appointments
    """
    db = get_db()
    row = db.execute(
        """
        SELECT COUNT(*) AS total_no_shows
        FROM appointments
        WHERE status = 'NO_SHOW'
        """
    ).fetchone()

    return jsonify(
        total_no_shows=row["total_no_shows"]
    )


@metrics_bp.route("/penalties", methods=["GET"])
@require_role("admin")
def penalties_per_patient():
    """
    Penalty counts grouped by patient
    """
    db = get_db()
    rows = db.execute(
        """
        SELECT
            patient_id,
            COUNT(*) AS penalty_count
        FROM patient_no_show_penalties
        GROUP BY patient_id
        ORDER BY penalty_count DESC
        """
    ).fetchall()

    return jsonify([
        {
            "patient_id": row["patient_id"],
            "penalty_count": row["penalty_count"]
        }
        for row in rows
    ])


@metrics_bp.route("/doctor-no-shows", methods=["GET"])
@require_role("admin")
def doctor_no_shows():
    """
    NO_SHOW counts grouped by doctor
    """
    db = get_db()
    rows = db.execute(
        """
        SELECT
            doctor_id,
            COUNT(*) AS no_show_count
        FROM appointments
        WHERE status = 'NO_SHOW'
        GROUP BY doctor_id
        ORDER BY no_show_count DESC
        """
    ).fetchall()

    return jsonify([
        {
            "doctor_id": row["doctor_id"],
            "no_show_count": row["no_show_count"]
        }
        for row in rows
    ])
