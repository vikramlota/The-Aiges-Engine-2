def test_signup_success(client):
    res = client.post("/api/auth/signup", json={"email": "newuser@example.com", "password": "securepassword123"})
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "created_at" in data


def test_signup_duplicate_email(client):
    client.post("/api/auth/signup", json={"email": "dup@example.com", "password": "password123"})
    res = client.post("/api/auth/signup", json={"email": "dup@example.com", "password": "password123"})
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_signup_short_password(client):
    res = client.post("/api/auth/signup", json={"email": "short@example.com", "password": "123"})
    assert res.status_code == 422


def test_login_success(client):
    client.post("/api/auth/signup", json={"email": "login@example.com", "password": "mypassword123"})
    res = client.post(
        "/api/auth/login",
        data={"username": "login@example.com", "password": "mypassword123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post("/api/auth/signup", json={"email": "wrongpwd@example.com", "password": "correctpassword123"})
    res = client.post(
        "/api/auth/login",
        data={"username": "wrongpwd@example.com", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["detail"]


def test_get_me(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "testuser@example.com"


def test_get_me_unauthorized(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
