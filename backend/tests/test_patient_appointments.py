from datetime import datetime, timedelta


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def get_doctor_id(client):
    from backend.db import get_db
    with client.application.app_context():
        row = get_db().execute(
            "SELECT user_id FROM doctors LIMIT 1"
        ).fetchone()
        return row["user_id"]


def test_patient_can_book_and_cancel(client):
    # register + login
    client.post(
        "/patient/register",
        json={"username": "p2_appt_unique", "password": "p123"}
    )
    login = client.post(
        "/patient/login",
        json={"username": "p2_appt_unique", "password": "p123"}
    )
    token = login.get_json()["token"]

    doctor_id = get_doctor_id(client)

    # IMPORTANT:
    # Push appointment far enough into the future
    # to avoid overlap with any other test data
    start = (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat()
    end = (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat()

    # book
    res = client.post(
        "/patient/appointments",
        json={
            "doctor_id": doctor_id,
            "start_datetime": start,
            "end_datetime": end
        },
        headers=auth_header(token)
    )
    assert res.status_code == 201

    # list
    res = client.get(
        "/patient/appointments",
        headers=auth_header(token)
    )
    data = res.get_json()
    assert len(data) >= 1

    appt_id = data[-1]["appointment_id"]

    # cancel
    res = client.patch(
        f"/patient/appointments/{appt_id}/cancel",
        headers=auth_header(token)
    )
    assert res.status_code == 200
    assert res.get_json()["status"] == "CANCELLED_BY_PATIENT" 
