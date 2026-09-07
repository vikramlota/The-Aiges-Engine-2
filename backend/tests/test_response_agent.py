import pytest


def test_draft_reply_unauthorized(client):
    res = client.post("/api/mentions/1/draft-reply", json={})
    assert res.status_code == 401


def test_draft_reply_and_approval_lifecycle(client, auth_headers):
    # 1. Ingest a severe complaint mention
    ingest_res = client.post(
        "/api/mentions/ingest",
        json={
            "post_id": "test_post_review",
            "comments": [
                {
                    "text": "Total scam product! It broke on arrival and your team cheated me!",
                    "author_handle": "@angry_customer"
                }
            ]
        },
        headers=auth_headers
    )
    assert ingest_res.status_code == 201
    mentions = ingest_res.json()
    mention_id = mentions[0]["id"]
    assert mentions[0]["drafted_reply"] is None
    assert mentions[0]["approved_at"] is None

    # 2. Generate a suggested response draft
    draft_res = client.post(
        f"/api/mentions/{mention_id}/draft-reply",
        json={"brand_name": "Acme Brand"},
        headers=auth_headers
    )
    assert draft_res.status_code == 200
    draft_data = draft_res.json()
    assert draft_data["mention_id"] == mention_id
    assert "@angry_customer" in draft_data["drafted_reply"] or "DM" in draft_data["drafted_reply"]
    assert "explanation" in draft_data["draft_explanation"].lower() or "strategy" in draft_data["draft_explanation"].lower()

    # Verify that generating a draft did NOT auto-approve it
    get_res = client.get(f"/api/mentions?post_id=test_post_review", headers=auth_headers)
    assert get_res.status_code == 200
    fetched_mention = get_res.json()[0]
    assert fetched_mention["drafted_reply"] is not None
    assert fetched_mention["approved_at"] is None
    assert fetched_mention["approved_by"] is None

    # 3. Explicit human approval with inline edit
    custom_edit = "Hi @angry_customer, we are so sorry. Please DM us your Order ID directly so our manager can assist."
    approve_res = client.post(
        f"/api/mentions/{mention_id}/approve",
        json={"edited_reply": custom_edit},
        headers=auth_headers
    )
    assert approve_res.status_code == 200
    app_data = approve_res.json()
    assert app_data["status"] == "APPROVED"
    assert app_data["drafted_reply"] == custom_edit
    assert app_data["approved_at"] is not None
    assert app_data["approved_by"] is not None

    # 4. Verify persisted state
    get_res2 = client.get(f"/api/mentions?post_id=test_post_review", headers=auth_headers)
    updated_mention = get_res2.json()[0]
    assert updated_mention["drafted_reply"] == custom_edit
    assert updated_mention["approved_at"] is not None


def test_draft_and_approve_user_isolation(client, auth_headers):
    # User 1 ingests a mention
    ingest_res = client.post(
        "/api/mentions/ingest",
        json={
            "post_id": "isolated_post",
            "comments": [{"text": "Broken bottle, refund please!", "author_handle": "@buyer_x"}]
        },
        headers=auth_headers
    )
    mention_id = ingest_res.json()[0]["id"]

    # User 2 logs in
    client.post("/api/auth/signup", json={"email": "hacker@example.com", "password": "password123"})
    login_res = client.post(
        "/api/auth/login",
        data={"username": "hacker@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    user2_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # User 2 attempts to draft or approve User 1's mention -> 404 Not Found
    draft_attack = client.post(f"/api/mentions/{mention_id}/draft-reply", json={}, headers=user2_headers)
    assert draft_attack.status_code == 404

    approve_attack = client.post(f"/api/mentions/{mention_id}/approve", json={}, headers=user2_headers)
    assert approve_attack.status_code == 404
