import sqlite3
import os
from werkzeug.security import generate_password_hash


def get_db_path():
    return os.getenv(
        "HMS_DB_PATH",
        os.path.join(os.path.dirname(__file__), "hms.db")
    )


def init_db():
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()

    cur.executescript("""
    -- =========================
    -- USERS TABLE
    -- =========================
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK(role IN ('admin','doctor','patient')) NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- =========================
    -- DOCTORS TABLE
    -- =========================
    CREATE TABLE IF NOT EXISTS doctors (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        specialization TEXT NOT NULL,
        is_blacklisted INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    -- =========================
    -- PATIENTS TABLE
    -- =========================
    CREATE TABLE IF NOT EXISTS patients (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    -- =========================
    -- DOCTOR AVAILABILITY
    -- =========================
    CREATE TABLE IF NOT EXISTS doctor_availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        start_datetime TEXT NOT NULL,
        end_datetime TEXT NOT NULL,
        is_available INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doctor_id) REFERENCES doctors(user_id)
    );

    -- =========================
    -- APPOINTMENTS
    -- =========================
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        start_datetime TEXT NOT NULL,
        end_datetime TEXT NOT NULL,
        status TEXT CHECK(
            status IN (
                'BOOKED',
                'COMPLETED',
                'CANCELLED_BY_ADMIN',
                'CANCELLED_BY_PATIENT',
                'NO_SHOW'
            )
        ) DEFAULT 'BOOKED',
        diagnosis TEXT,
        treatment TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES users(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(user_id),
        UNIQUE (doctor_id, start_datetime)
    );

    -- =========================
    -- PATIENT NO-SHOW PENALTIES
    -- =========================
    CREATE TABLE IF NOT EXISTS patient_no_show_penalties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER UNIQUE NOT NULL,
        patient_id INTEGER NOT NULL,
        email_sent INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id),
        FOREIGN KEY (patient_id) REFERENCES users(id)
    );

    -- =========================
    -- AUDIT LOG TABLE
    -- =========================
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor_role TEXT NOT NULL,
        actor_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        metadata TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # =========================
    # SEED ADMIN USER
    # =========================
    cur.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", generate_password_hash("admin123"), "admin")
        )

    # =========================
    # SEED TEST DOCTOR
    # =========================
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

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()

