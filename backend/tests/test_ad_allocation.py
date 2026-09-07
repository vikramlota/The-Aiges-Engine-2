import pytest


def test_campaign_create_unauthorized(client):
    res = client.post("/api/campaigns", json={"name": "Festive Push"})
    assert res.status_code == 401


def test_campaign_lifecycle_and_bandit_optimization(client, auth_headers):
    # 1. Create campaign with initial channels
    campaign_payload = {
        "name": "Q4 Festive Growth",
        "total_monthly_budget": 100000.0,
        "currency": "INR",
        "channels": [
            {
                "name": "Instagram Reels",
                "current_allocation_pct": 25.0,
                "current_spend": 25000.0,
                "impressions": 120000,
                "clicks": 3000,
                "conversions": 180,
                "revenue": 95000.0
            },
            {
                "name": "Meta Feed",
                "current_allocation_pct": 45.0,
                "current_spend": 45000.0,
                "impressions": 180000,
                "clicks": 2200,
                "conversions": 50,
                "revenue": 52000.0
            },
            {
                "name": "YouTube Shorts",
                "current_allocation_pct": 30.0,
                "current_spend": 30000.0,
                "impressions": 110000,
                "clicks": 2500,
                "conversions": 110,
                "revenue": 78000.0
            }
        ]
    }
    create_res = client.post("/api/campaigns", json=campaign_payload, headers=auth_headers)
    assert create_res.status_code == 201
    campaign_data = create_res.json()
    campaign_id = campaign_data["id"]
    assert len(campaign_data["channels"]) == 3

    # 2. Get campaign detail
    get_res = client.get(f"/api/campaigns/{campaign_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Q4 Festive Growth"

    # 3. Trigger Thompson Sampling optimization recommendation
    rec_res = client.post(f"/api/campaigns/{campaign_id}/recommend", headers=auth_headers)
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    rec_id = rec_data["id"]

    assert rec_data["status"] == "PENDING"
    assert rec_data["approved_at"] is None
    assert rec_data["approved_by"] is None
    assert rec_data["confidence"] > 0.6
    assert len(rec_data["shifts"]) == 3
    assert "Thompson Sampling" in rec_data["reasoning"]

    # Top performing channel should be recommended a budget increase
    top_shift = rec_data["shifts"][0]
    assert top_shift["channel_name"] in ["Instagram Reels", "YouTube Shorts"]
    assert top_shift["delta_pct"] > 0

    # 4. Approve recommendation
    approve_res = client.post(f"/api/recommendations/{rec_id}/approve", json={}, headers=auth_headers)
    assert approve_res.status_code == 200
    app_data = approve_res.json()
    assert app_data["status"] == "APPROVED"
    assert app_data["approved_at"] is not None
    assert app_data["approved_by"] is not None

    # Verify channel allocations updated in campaign
    updated_campaign = client.get(f"/api/campaigns/{campaign_id}", headers=auth_headers).json()
    ch_dict = {c["name"]: c["current_allocation_pct"] for c in updated_campaign["channels"]}
    assert ch_dict[top_shift["channel_name"]] == top_shift["suggested_pct"]


def test_ad_allocation_user_isolation(client, auth_headers):
    # User 1 creates a campaign
    res1 = client.post(
        "/api/campaigns",
        json={"name": "User 1 Campaign", "total_monthly_budget": 50000.0},
        headers=auth_headers
    )
    camp_id = res1.json()["id"]

    # User 2 logs in
    client.post("/api/auth/signup", json={"email": "ad_intruder@example.com", "password": "password123"})
    login_res = client.post(
        "/api/auth/login",
        data={"username": "ad_intruder@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    user2_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # User 2 cannot access or recommend User 1's campaign
    get_res = client.get(f"/api/campaigns/{camp_id}", headers=user2_headers)
    assert get_res.status_code == 404

    rec_res = client.post(f"/api/campaigns/{camp_id}/recommend", headers=user2_headers)
    assert rec_res.status_code == 404
