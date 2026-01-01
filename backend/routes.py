from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash,generate_password_hash
from backend.db import get_db
from backend.config import SECRET_KEY, JWT_ALGO, JWT_EXP_SECONDS
from datetime import datetime, timedelta
import jwt
from functools import wraps

def log_audit(action, entity_type, entity_id, metadata=None):
    db = get_db()
    db.execute(
        """
        INSERT INTO audit_logs
        (actor_role, actor_id, action, entity_type, entity_id, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            request.user_role,
            request.user_id,
            action,
            entity_type,
            entity_id,
            metadata
        )
    )
    db.commit()


health_bp = Blueprint("health", __name__)
auth_bp = Blueprint("auth", __name__)

def require_role(expected_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify(error="Missing or invalid Authorization header"), 401

            token = auth_header.split(" ", 1)[1]

            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGO])
            except jwt.ExpiredSignatureError:
                return jsonify(error="Token expired"), 401
            except Exception:
                return jsonify(error="Invalid token"), 401

            if payload.get("role") != expected_role:
                return jsonify(error="Forbidden"), 403

            request.user_id = payload["sub"]
            request.user_role = payload["role"]

            return fn(*args, **kwargs)
        return wrapper
    return decorator

@health_bp.route("/health", methods=["GET"])
def health():
    db = get_db()
    db.execute("SELECT 1")
    return jsonify(status="ok", db="connected")

@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify(error="Username and password required"), 400

    db = get_db()
    row = db.execute(
        "SELECT id, password_hash FROM users WHERE username=? AND role='admin' AND is_active=1",
        (username,)
    ).fetchone()

    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    payload = {
        "sub": str(row["id"]),
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_SECONDS)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGO)

    return jsonify(
        admin_id=row["id"],
        token=token,
        message="Admin login successful"
    )

@auth_bp.route("/admin/me", methods=["GET"])
@require_role("admin")
def admin_me():
    return jsonify(
        admin_id=request.user_id,
        role="admin"
    )

@auth_bp.route("/admin/stats/doctors/count", methods=["GET"])
@require_role("admin")
def admin_doctor_count():
    db = get_db()
    row = db.execute("SELECT COUNT(*) AS count FROM doctors").fetchone()
    return jsonify(count=row["count"])

@auth_bp.route("/admin/stats/patients/count", methods=["GET"])
@require_role("admin")
def admin_patient_count():
    db = get_db()
    row = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM users
        WHERE role = 'patient'
          AND is_active = 1
        """
    ).fetchone()

    return jsonify(count=row["count"])


@auth_bp.route("/admin/stats/appointments/today", methods=["GET"])
@require_role("admin")
def admin_appointments_today_count():
    db = get_db()

    row = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM appointments
        WHERE date(start_datetime) = date('now')
        """
    ).fetchone()

    return jsonify(count=row["count"])


@auth_bp.route("/admin/appointments/<int:appointment_id>/cancel", methods=["POST"])
@require_role("admin")
def admin_cancel_appointment(appointment_id):
    db = get_db()

    appt = db.execute(
        "SELECT status FROM appointments WHERE id = ?",
        (appointment_id,)
    ).fetchone()

    if not appt:
        return jsonify(error="Appointment not found"), 404

    if appt["status"] == "CANCELLED":
        return jsonify(
            message="Appointment already cancelled",
            appointment_id=appointment_id,
            status="CANCELLED"
        )

    db.execute(
        """
        UPDATE appointments
        SET status = 'CANCELLED'
        WHERE id = ?
        """,
        (appointment_id,)
    )
    db.commit()
    
    log_audit(
        action="CANCEL_APPOINTMENT",
        entity_type="appointment",
        entity_id=appointment_id
    )


    return jsonify(
        message="Appointment cancelled by admin",
        appointment_id=appointment_id,
        status="CANCELLED"
    )


@auth_bp.route("/admin/appointments/<int:appointment_id>/mark-no-show", methods=["POST"])
@require_role("admin")
def admin_mark_no_show(appointment_id):
    db = get_db()

    appt = db.execute(
        "SELECT status FROM appointments WHERE id = ?",
        (appointment_id,)
    ).fetchone()

    if not appt:
        return jsonify(error="Appointment not found"), 404

    if appt["status"] == "NO_SHOW":
        return jsonify(
            message="Appointment already marked as NO_SHOW",
            appointment_id=appointment_id,
            status="NO_SHOW"
        )

    db.execute(
        """
        UPDATE appointments
        SET status = 'NO_SHOW'
        WHERE id = ?
        """,
        (appointment_id,)
    )
    db.commit()
    
    log_audit(
        action="MARK_NO_SHOW",
        entity_type="appointment",
        entity_id=appointment_id
    )


    return jsonify(
        message="Appointment marked as NO_SHOW by admin",
        appointment_id=appointment_id,
        status="NO_SHOW"
    )


@auth_bp.route("/admin/appointments", methods=["GET"])
@require_role("admin")
def admin_view_appointments():
    db = get_db()

    query = """
        SELECT
            a.id AS appointment_id,
            a.patient_id,
            p.name AS patient_name,
            a.doctor_id,
            d.name AS doctor_name,
            a.start_datetime,
            a.end_datetime,
            a.status,
            substr(a.start_datetime, 1, 10) AS appt_date
        FROM appointments a
        JOIN patients p ON p.user_id = a.patient_id
        JOIN doctors d ON d.user_id = a.doctor_id
        ORDER BY a.start_datetime
    """

    rows = db.execute(query).fetchall()
    return jsonify([dict(row) for row in rows])



@auth_bp.route("/admin/doctors/<int:doctor_id>/blacklist", methods=["POST"])
@require_role("admin")
def blacklist_doctor(doctor_id):
    db = get_db()

    doctor = db.execute(
        "SELECT user_id FROM doctors WHERE user_id = ?",
        (doctor_id,)
    ).fetchone()

    if not doctor:
        return jsonify(error="Doctor not found"), 404

    db.execute(
        """
        UPDATE doctors
        SET is_blacklisted = 1
        WHERE user_id = ?
        """,
        (doctor_id,)
    )
    db.commit()

    return jsonify(
        message="Doctor blacklisted",
        doctor_id=doctor_id,
        is_blacklisted=True
    )

@auth_bp.route("/admin/doctors/<int:doctor_id>/unblacklist", methods=["POST"])
@require_role("admin")
def unblacklist_doctor(doctor_id):
    db = get_db()

    doctor = db.execute(
        "SELECT user_id FROM doctors WHERE user_id = ?",
        (doctor_id,)
    ).fetchone()

    if not doctor:
        return jsonify(error="Doctor not found"), 404

    db.execute(
        """
        UPDATE doctors
        SET is_blacklisted = 0
        WHERE user_id = ?
        """,
        (doctor_id,)
    )
    db.commit()

    return jsonify(
        message="Doctor unblacklisted",
        doctor_id=doctor_id,
        is_blacklisted=False
    )

@auth_bp.route("/admin/appointments/mark-no-shows", methods=["POST"])
@require_role("admin")
def mark_no_shows():
    db = get_db()

    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")

    cursor = db.execute(
        """
        UPDATE appointments
        SET status = 'NO_SHOW'
        WHERE status = 'BOOKED'
          AND end_datetime < ?
        """,
        (now,)
    )

    db.commit()

    return jsonify(
        message="NO_SHOW automation completed",
        no_shows_marked=cursor.rowcount
    )


@auth_bp.route("/doctor/login", methods=["POST"])
def doctor_login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify(error="Username and password required"), 400

    db = get_db()
    row = db.execute(
        """
        SELECT u.id, u.password_hash, d.is_blacklisted
        FROM users u
        JOIN doctors d ON d.user_id = u.id
        WHERE u.username = ?
          AND u.role = 'doctor'
          AND u.is_active = 1
        """,
        (username,)
    ).fetchone()

    if not row:
        return jsonify(error="Invalid credentials"), 401

    if row["is_blacklisted"]:
        return jsonify(error="Doctor is blacklisted"), 403

    if not check_password_hash(row["password_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    payload = {
        "sub": str(row["id"]),
        "role": "doctor",
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_SECONDS)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGO)

    return jsonify(
        doctor_id=row["id"],
        token=token,
        message="Doctor login successful"
    )
    

@auth_bp.route("/doctor/register", methods=["POST"])
def doctor_register():
    data = request.get_json() or {}

    username = data.get("username")
    password = data.get("password")
    name = data.get("name")
    specialization = data.get("specialization")

    if not username or not password or not name:
        return jsonify(error="Missing required fields"), 400

    db = get_db()

    # prevent duplicate username
    existing = db.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if existing:
        return jsonify(error="Username already exists"), 409

    # create user
    password_hash = generate_password_hash(password)

    cursor = db.execute(
        """
        INSERT INTO users (username, password_hash, role)
        VALUES (?, ?, 'doctor')
        """,
        (username, password_hash)
    )

    doctor_user_id = cursor.lastrowid

    # create doctor profile
    db.execute(
        """
        INSERT INTO doctors (user_id, name, specialization)
        VALUES (?, ?, ?)
        """,
        (doctor_user_id, name, specialization)
    )

    db.commit()

    return jsonify(
        message="Doctor registered successfully",
        doctor_id=doctor_user_id
    ), 201


@auth_bp.route("/doctor/me", methods=["GET"])
@require_role("doctor")
def doctor_me():
    return jsonify(
        doctor_id=request.user_id,
        role="doctor"
    )

@auth_bp.route("/doctor/availability", methods=["POST"])
@require_role("doctor")
def create_availability():
    data = request.get_json() or {}

    availability_date = data.get("date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    if not availability_date or not start_time or not end_time:
        return jsonify(error="Missing required fields"), 400

    db = get_db()
    db.execute(
        """
        INSERT INTO doctor_availability (doctor_id, date, start_time, end_time)
        VALUES (?, ?, ?, ?)
        """,
        (request.user_id, availability_date, start_time, end_time)
    )
    db.commit()

    return jsonify(
        message="Availability created",
        doctor_id=request.user_id,
        date=availability_date,
        start_time=start_time,
        end_time=end_time
    ), 201

@auth_bp.route("/doctor/availability", methods=["GET"])
@require_role("doctor")
def get_doctor_availability():
    db = get_db()
    rows = db.execute(
        """
        SELECT id, date, start_time, end_time
        FROM doctor_availability
        WHERE doctor_id = ?
        ORDER BY date, start_time
        """,
        (request.user_id,)
    ).fetchall()

    return jsonify([
        {
            "id": row["id"],
            "date": row["date"],
            "start_time": row["start_time"],
            "end_time": row["end_time"]
        }
        for row in rows
    ])


@auth_bp.route("/doctor/appointments", methods=["GET"])
@require_role("doctor")
def get_doctor_appointments():
    db = get_db()

    status = request.args.get("status")
    date = request.args.get("date")  # YYYY-MM-DD

    query = """
        SELECT
            id AS appointment_id,
            patient_id,
            start_datetime,
            end_datetime,
            status
        FROM appointments
        WHERE doctor_id = ?
    """
    params = [request.user_id]

    if status:
        query += " AND status = ?"
        params.append(status)

    if date:
        query += " AND substr(start_datetime, 1, 10) = ?"
        params.append(date)

    query += " ORDER BY start_datetime"

    rows = db.execute(query, params).fetchall()

    return jsonify([
        {
            "appointment_id": row["appointment_id"],
            "patient_id": row["patient_id"],
            "start_datetime": row["start_datetime"],
            "end_datetime": row["end_datetime"],
            "status": row["status"]
        }
        for row in rows
    ])

@auth_bp.route("/admin/stats/appointments/no-shows", methods=["GET"])
@require_role("admin")
def admin_no_shows_count():
    db = get_db()

    row = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM appointments
        WHERE status = 'NO_SHOW'
        """
    ).fetchone()

    return jsonify(count=row["count"])

@auth_bp.route("/admin/stats/appointments/cancelled", methods=["GET"])
@require_role("admin")
def admin_cancelled_appointments_count():
    db = get_db()

    row = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM appointments
        WHERE status = 'CANCELLED'
        """
    ).fetchone()

    return jsonify(count=row["count"])
@auth_bp.route("/patient/register", methods=["POST"])
def patient_register():
    data = request.get_json() or {}

    username = data.get("username")
    password = data.get("password")
    name = data.get("name")
    age = data.get("age")
    gender = data.get("gender")

    if not username or not password or not name:
        return jsonify(error="Missing required fields"), 400

    db = get_db()

    # prevent duplicate username
    existing = db.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if existing:
        return jsonify(error="Username already exists"), 409

    password_hash = generate_password_hash(password)

    cursor = db.execute(
        """
        INSERT INTO users (username, password_hash, role)
        VALUES (?, ?, 'patient')
        """,
        (username, password_hash)
    )

    patient_user_id = cursor.lastrowid

    db.execute(
        """
        INSERT INTO patients (user_id, name, age, gender)
        VALUES (?, ?, ?, ?)
        """,
        (patient_user_id, name, age, gender)
    )

    db.commit()

    return jsonify(
        message="Patient registered successfully",
        patient_id=patient_user_id
    ), 201


@auth_bp.route("/patient/appointments", methods=["POST"])
@require_role("patient")
def book_appointment():
    data = request.get_json() or {}

    doctor_id = data.get("doctor_id")
    start_datetime = data.get("start_datetime")
    end_datetime = data.get("end_datetime")

    if not all([doctor_id, start_datetime, end_datetime]):
        return jsonify(error="Missing required fields"), 400

    db = get_db()

    # conflict check
    conflict = db.execute(
        """
        SELECT 1 FROM appointments
        WHERE doctor_id = ?
          AND status = 'BOOKED'
          AND NOT (
            end_datetime <= ?
            OR start_datetime >= ?
          )
        """,
        (doctor_id, start_datetime, end_datetime)
    ).fetchone()

    if conflict:
        return jsonify(error="Doctor already has an appointment in this time slot"), 409

    db.execute(
        """
        INSERT INTO appointments
        (patient_id, doctor_id, start_datetime, end_datetime, status)
        VALUES (?, ?, ?, ?, 'BOOKED')
        """,
        (request.user_id, doctor_id, start_datetime, end_datetime)
    )
    db.commit()
    
    patient_email = "venkateshrr.19@gmail.com"
    
    from backend.tasks import send_email_task
    
    send_email_task.delay(
    patient_email,
    "Appointment Booked",
    "Your appointment has been successfully booked."
   )


    return jsonify(
        message="Appointment booked",
        doctor_id=doctor_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        status="BOOKED"
    ), 201


@auth_bp.route("/patient/appointments", methods=["GET"])
@require_role("patient")
def get_patient_appointments():
    db = get_db()
    status = request.args.get("status")
    date = request.args.get("date")  # YYYY-MM-DD

    query = """
    SELECT
        a.id,
        a.doctor_id,
        d.name AS doctor_name,
        d.specialization,
        a.start_datetime,
        a.end_datetime,
        a.status,
        a.diagnosis,
        a.treatment
    FROM appointments a
    JOIN doctors d ON d.user_id = a.doctor_id
    WHERE a.patient_id = ?
    """
    params = [request.user_id]

    if status:
        query += " AND a.status = ?"
        params.append(status)

    if date:
        query += " AND substr(a.start_datetime, 1, 10) = ?"
        params.append(date)

    query += " ORDER BY a.start_datetime DESC"

    rows = db.execute(query, params).fetchall()


    return jsonify([
        {
            "appointment_id": row["id"],
            "doctor_id": row["doctor_id"],
            "doctor_name": row["doctor_name"],
            "specialization": row["specialization"],
            "start_datetime": row["start_datetime"],
            "end_datetime": row["end_datetime"],
            "status": row["status"],
            "diagnosis": row["diagnosis"],
            "treatment": row["treatment"]
        }
        for row in rows
    ])


@auth_bp.route("/patient/login", methods=["POST"])
def patient_login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify(error="Username and password required"), 400

    db = get_db()
    row = db.execute(
        """
        SELECT id, password_hash
        FROM users
        WHERE username = ?
          AND role = 'patient'
          AND is_active = 1
        """,
        (username,)
    ).fetchone()

    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify(error="Invalid credentials"), 401

    payload = {
        "sub": str(row["id"]),
        "role": "patient",
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXP_SECONDS)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGO)

    return jsonify(
        patient_id=row["id"],
        token=token,
        message="Patient login successful"
    )

@auth_bp.route("/patient/appointments/<int:appointment_id>/cancel", methods=["POST"])
@require_role("patient")
def cancel_appointment(appointment_id):
    db = get_db()

    appt = db.execute(
        """
        SELECT id FROM appointments
        WHERE id = ?
          AND patient_id = ?
          AND status = 'BOOKED'
        """,
        (appointment_id, request.user_id)
    ).fetchone()

    if not appt:
        return jsonify(error="Appointment not found or cannot be cancelled"), 404

    db.execute(
        """
        UPDATE appointments
        SET status = 'CANCELLED'
        WHERE id = ?
        """,
        (appointment_id,)
    )
    db.commit()

    return jsonify(
        message="Appointment cancelled",
        appointment_id=appointment_id,
        status="CANCELLED"
    )



@auth_bp.route("/doctor/appointments/<int:appointment_id>/complete", methods=["POST"])
@require_role("doctor")
def complete_appointment(appointment_id):
    data = request.get_json() or {}
    diagnosis = data.get("diagnosis")
    treatment = data.get("treatment")

    if not diagnosis or not treatment:
        return jsonify(error="Diagnosis and treatment are required"), 400

    db = get_db()

    appt = db.execute(
        """
        SELECT id FROM appointments
        WHERE id = ?
          AND doctor_id = ?
          AND status = 'BOOKED'
        """,
        (appointment_id, request.user_id)
    ).fetchone()

    if not appt:
        return jsonify(error="Appointment not found or not allowed"), 404

    db.execute(
        """
        UPDATE appointments
        SET status = 'COMPLETED',
            diagnosis = ?,
            treatment = ?
        WHERE id = ?
        """,
        (diagnosis, treatment, appointment_id)
    )
    db.commit()

    return jsonify(
        message="Appointment marked as completed",
        appointment_id=appointment_id,
        status="COMPLETED"
    )

