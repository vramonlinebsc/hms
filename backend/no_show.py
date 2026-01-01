# backend/no_show.py

from datetime import datetime, timedelta
from backend.db import get_db


def mark_no_show_appointments(now: datetime, grace_minutes: int) -> int:
    """
    Mark eligible appointments as NO_SHOW.

    Rules:
    - status must be BOOKED
    - end_datetime < now - grace_minutes
    - one-way transition: BOOKED -> NO_SHOW
    - idempotent (safe to run repeatedly)
    - audit written only on successful transition

    Returns:
        int: number of appointments marked as NO_SHOW
    """

    db = get_db()

    cutoff = now - timedelta(minutes=grace_minutes)

    # Find eligible appointments
    rows = db.execute(
        """
        SELECT id
        FROM appointments
        WHERE status = 'BOOKED'
          AND end_datetime < ?
        """,
        (cutoff.isoformat(),)
    ).fetchall()

    if not rows:
        return 0

    appointment_ids = [row["id"] for row in rows]

    # Update appointments to NO_SHOW
    db.executemany(
        """
        UPDATE appointments
        SET status = 'NO_SHOW'
        WHERE id = ?
          AND status = 'BOOKED'
        """,
        [(aid,) for aid in appointment_ids]
    )

    # Write audit logs for successful transitions
    db.executemany(
        """
        INSERT INTO audit_logs (
            actor_role,
            actor_id,
            action,
            appointment_id
        )
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                "admin",
                None,
                "ADMIN_MARKED_NO_SHOW",
                aid,
            )
            for aid in appointment_ids
        ]
    )

    db.commit()

    return len(appointment_ids)

