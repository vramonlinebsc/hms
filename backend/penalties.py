from backend.db import get_db
from backend.tasks import send_email_task


def apply_no_show_penalties():
    """
    Insert penalties for NO_SHOW appointments exactly once,
    and enqueue email only once per penalty.
    """

    db = get_db()

    # 1) Insert penalties idempotently
    db.execute(
        """
        INSERT OR IGNORE INTO patient_no_show_penalties (appointment_id, patient_id)
        SELECT
            a.id,
            a.patient_id
        FROM appointments a
        WHERE a.status = 'NO_SHOW'
        """
    )

    # 2) Find penalties that have not yet triggered email
    rows = db.execute(
        """
        SELECT
            p.id AS penalty_id,
            u.username AS email
        FROM patient_no_show_penalties p
        JOIN users u ON u.id = p.patient_id
        WHERE p.email_sent = 0
        """
    ).fetchall()

    # 3) Enqueue email + mark as sent
    for row in rows:
        send_email_task.delay(
            to_email=row["email"],
            subject="Appointment No-Show Recorded",
            body=(
                "You missed a scheduled appointment. "
                "If this was an error, please contact the clinic."
            ),
        )

        db.execute(
            """
            UPDATE patient_no_show_penalties
            SET email_sent = 1
            WHERE id = ?
            """,
            (row["penalty_id"],)
        )

    db.commit()
