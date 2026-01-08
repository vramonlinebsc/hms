from flask import Blueprint, jsonify, request
from datetime import datetime

from backend.db import get_db
from backend.routes import require_role

# MUST exist at top level
doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")


@doctor_bp.route("/slots", methods=["POST"])
@require_role("doctor")
def create_slot():
    data = request.get_json() or {}
    start = data.get("start_datetime")
    end = data.get("end_datetime")

    if not start or not end:
        return jsonify(error="Missing start or end datetime"), 400

    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
    except ValueError:
        return jsonify(error="Invalid datetime format"), 400

    if start_dt >= end_dt:
        return jsonify(error="Invalid time range"), 400

    if start_dt <= datetime.utcnow():
        return jsonify(error="Slot must be in the future"), 400

    db = get_db()
    try:
        cur = db.execute(
            """
            INSERT INTO doctor_slots (doctor_id, start_datetime, end_datetime)
            VALUES (?, ?, ?)
            """,
            (request.user_id, start, end)
        )
        db.commit()
    except Exception:
        return jsonify(error="Slot already exists"), 409

    return jsonify(
        slot_id=cur.lastrowid,
        doctor_id=request.user_id,
        start_datetime=start,
        end_datetime=end
    ), 201
