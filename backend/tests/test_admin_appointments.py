from datetime import datetime, timedelta

def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def get_admin_token(client):
    res = client.post(
        "/admin/login",
        json={"username": "admin", "password": "admin123"}
    )
    return res.get_json()["token"]


def test_admin_can_cancel_appointment(client):
    # patient setup
    client.post("/patient/register", json={"username": "p3", "password": "p123"})
    login = client.post("/patient/login", json={"username": "p3", "password": "p123"})
    ptoken = login.get_json()["token"]

    start = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    end = (datetime.utcnow() + timedelta(hours=2)).isoformat()

    client.post(
        "/patient/appointments",
        json={
            "doctor_id": 2,
            "start_datetime": start,
            "end_datetime": end
        },
        headers=auth_header(ptoken)
    )

    admin_token = get_admin_token(client)

    # list
    res = client.get(
        "/admin/appointments",
        headers=auth_header(admin_token)
    )
    appt_id = res.get_json()[0]["appointment_id"]

    # cancel
    res = client.patch(
        f"/admin/appointments/{appt_id}/cancel",
        headers=auth_header(admin_token)
    )
    assert res.status_code == 200
    assert res.get_json()["status"] == "CANCELLED_BY_ADMIN"

