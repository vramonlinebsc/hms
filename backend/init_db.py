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

    # ---- HARD RESET (SAFE FOR HMS PROJECT) ----
    cur.executescript("""
    DROP TABLE IF EXISTS audit_logs;
    DROP TABLE IF EXISTS patient_no_show_penalties;
    DROP TABLE IF EXISTS appointments;
    DROP TABLE IF EXISTS doctor_slots;
    DROP TABLE IF EXISTS patients;
    DROP TABLE IF EXISTS doctors;
    DROP TABLE IF EXISTS users;
    """)

    cur.executescript("""
    -- =========================
    -- USERS
    -- =========================
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT CHECK(role IN ('admin','doctor','patient')) NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- =========================
    -- DOCTORS
    -- =========================
    CREATE TABLE doctors (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        specialization TEXT NOT NULL,
        is_blacklisted INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    -- =========================
    -- PATIENTS
    -- =========================
    CREATE TABLE patients (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    -- =========================
    -- DOCTOR SLOTS
    -- =========================
    CREATE TABLE doctor_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id INTEGER NOT NULL,
        start_datetime TEXT NOT NULL,
        end_datetime TEXT NOT NULL,
        is_booked INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (doctor_id) REFERENCES doctors(user_id),
        UNIQUE (doctor_id, start_datetime)
    );

    -- =========================
    -- APPOINTMENTS
    -- =========================
    CREATE TABLE appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_id INTEGER NOT NULL UNIQUE,
        patient_id INTEGER NOT NULL,
        status TEXT CHECK (
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
        FOREIGN KEY (slot_id) REFERENCES doctor_slots(id),
        FOREIGN KEY (patient_id) REFERENCES users(id)
    );

    CREATE UNIQUE INDEX uq_patient_slot
    ON appointments (patient_id, slot_id);

    -- =========================
    -- NO-SHOW PENALTIES
    -- =========================
    CREATE TABLE patient_no_show_penalties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER UNIQUE NOT NULL,
        patient_id INTEGER NOT NULL,
        email_sent INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id),
        FOREIGN KEY (patient_id) REFERENCES users(id)
    );

    -- =========================
    -- AUDIT LOG
    -- =========================
    CREATE TABLE audit_logs (
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

    # ---- SEED ADMIN ----
    cur.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("admin", generate_password_hash("admin123"), "admin")
    )

    # ---- SEED DOCTOR ----
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

