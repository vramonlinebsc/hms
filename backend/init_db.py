import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "hms.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
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
        status TEXT CHECK(status IN ('BOOKED','COMPLETED','CANCELLED')) DEFAULT 'BOOKED',
        diagnosis TEXT,
        treatment TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES users(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(user_id),
        UNIQUE (doctor_id, start_datetime)
    );
    """)

    # =========================
    # SEED ADMIN USER
    # =========================
    cur.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        """, (
            "admin",
            generate_password_hash("admin123"),
            "admin"
        ))

    # =========================
    # SEED TEST DOCTOR
    # =========================
    cur.execute("SELECT id FROM users WHERE username = 'doctor1'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        """, (
            "doctor1",
            generate_password_hash("doctor123"),
            "doctor"
        ))

        doctor_user_id = cur.lastrowid

        cur.execute("""
            INSERT INTO doctors (user_id, name, specialization)
            VALUES (?, ?, ?)
        """, (
            doctor_user_id,
            "Dr. Test",
            "General Medicine"
        ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()

