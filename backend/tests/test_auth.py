def test_admin_login_success(client):
    res = client.post(
        "/admin/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert res.status_code == 200
    assert "token" in res.get_json()


def test_patient_register_and_login(client):
    res = client.post(
        "/patient/register",
        json={"username": "p1_auth", "password": "p123"}
    )
    assert res.status_code == 201

    res = client.post(
        "/patient/login",
        json={"username": "p1_auth", "password": "p123"}
    )
    assert res.status_code == 200
    assert "token" in res.get_json()

