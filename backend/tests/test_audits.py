def test_audit_unauthorized(client):
    res = client.post("/api/audits", json={
        "platform": "Instagram",
        "content_type": "static_post",
        "material_connection": "paid",
        "caption": "test"
    })
    assert res.status_code == 401


def test_audit_invalid_enums(client, auth_headers):
    # Invalid content_type
    res = client.post("/api/audits", json={
        "platform": "Instagram",
        "content_type": "invalid_type",
        "material_connection": "paid",
        "caption": "test"
    }, headers=auth_headers)
    assert res.status_code == 422
    assert "Invalid content_type" in res.json()["detail"]

    # Invalid material_connection
    res = client.post("/api/audits", json={
        "platform": "Instagram",
        "content_type": "static_post",
        "material_connection": "invalid_connection",
        "caption": "test"
    }, headers=auth_headers)
    assert res.status_code == 422
    assert "Invalid material_connection" in res.json()["detail"]


def test_audit_compliant_post(client, auth_headers):
    res = client.post("/api/audits", json={
        "platform": "Instagram",
        "content_type": "static_post",
        "material_connection": "paid",
        "caption": "#ad Loving this new skincare product from XYZ!"
    }, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "COMPLIANT"
    assert len(data["violations"]) == 0
    assert "id" in data


def test_audit_flagged_post(client, auth_headers):
    res = client.post("/api/audits", json={
        "platform": "Instagram",
        "content_type": "static_post",
        "material_connection": "paid",
        "caption": "#collab check out this cool gadget"
    }, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "FLAGGED"
    assert "approved_label" in data["violations"]
    assert "approved_label" in data["explanations"]


def test_audits_user_isolation(client, auth_headers):
    # 1. User 1 creates an audit
    res1 = client.post("/api/audits", json={
        "platform": "Instagram",
        "content_type": "static_post",
        "material_connection": "paid",
        "caption": "User 1 caption #ad"
    }, headers=auth_headers)
    assert res1.status_code == 201
    audit1_id = res1.json()["id"]

    # 2. Register & login User 2
    client.post("/api/auth/signup", json={"email": "user2@example.com", "password": "password123"})
    login_res2 = client.post(
        "/api/auth/login",
        data={"username": "user2@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    user2_headers = {"Authorization": f"Bearer {login_res2.json()['access_token']}"}

    # 3. User 2 lists audits -> should be empty
    list_res = client.get("/api/audits", headers=user2_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0

    # 4. User 2 tries to access User 1's audit -> MUST return 404 (not 403)
    get_res = client.get(f"/api/audits/{audit1_id}", headers=user2_headers)
    assert get_res.status_code == 404


def test_similar_past_audits(client, auth_headers):
    # First audit with similar topic
    res1 = client.post("/api/audits", json={
        "platform": "Instagram",
        "content_type": "static_post",
        "material_connection": "paid",
        "caption": "Check out this amazing organic hair serum #ad"
    }, headers=auth_headers)
    assert res1.status_code == 201

    # Second audit with similar text
    res2 = client.post("/api/audits", json={
        "platform": "Instagram",
        "content_type": "static_post",
        "material_connection": "paid",
        "caption": "Loving this organic hair serum routine #collab"
    }, headers=auth_headers)
    assert res2.status_code == 201
    data2 = res2.json()

    # Verify similar_past_audits contains the first audit
    assert "similar_past_audits" in data2
    assert len(data2["similar_past_audits"]) >= 1
    similar_ids = [item["id"] for item in data2["similar_past_audits"]]
    assert res1.json()["id"] in similar_ids
