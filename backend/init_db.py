import os
import sqlite3
from werkzeug.security import generate_password_hash


def get_db_path():
    return os.environ.get("HMS_DB_PATH", "hms.db")


def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS doctors (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        specialization TEXT,
        is_blacklisted INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS doctor_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        slot_time TEXT NOT NULL,
        is_booked INTEGER DEFAULT 0,
        FOREIGN KEY(doctor_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_id INTEGER NOT NULL,
        patient_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'booked',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(slot_id) REFERENCES doctor_slots(id),
        FOREIGN KEY(patient_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS appointment_audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER NOT NULL,
        actor_role TEXT NOT NULL,
        actor_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # seed admin
    cur.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", generate_password_hash("admin123"), "admin")
        )

    # seed doctor
    cur.execute("SELECT id FROM users WHERE username = 'doctor1'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("doctor1", generate_password_hash("doctor123"), "doctor")
        )
        doctor_user_id = cur.lastrowid

        cur.execute(
            "INSERT INTO doctors (user_id, name, specialization) VALUES (?, ?, ?)",
            (doctor_user_id, "Dr. Test", "General Medicine")
        )

    
    cur.executescript("""
    CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
    CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

    CREATE INDEX IF NOT EXISTS idx_doctors_blacklisted ON doctors(is_blacklisted);

     -- Appointments: only index columns that actually exist
    CREATE INDEX IF NOT EXISTS idx_appt_created_at ON appointments(created_at);
    CREATE INDEX IF NOT EXISTS idx_appt_slot ON appointments(slot_id);
    CREATE INDEX IF NOT EXISTS idx_appt_patient ON appointments(patient_id);
    CREATE INDEX IF NOT EXISTS idx_appt_status ON appointments(status);

    """)


    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
