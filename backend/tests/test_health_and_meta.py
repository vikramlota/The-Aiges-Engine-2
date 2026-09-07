def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_meta_endpoint(client):
    res = client.get("/api/meta")
    assert res.status_code == 200
    data = res.json()

    assert "platforms" in data
    assert "Instagram" in data["platforms"]
    assert "YouTube" in data["platforms"]

    assert "content_types" in data
    assert "static_post" in data["content_types"]
    assert "reel_story" in data["content_types"]

    assert "material_connections" in data
    assert len(data["material_connections"]) > 0
    keys = [item["key"] for item in data["material_connections"]]
    assert "paid" in keys
    assert "gifted_barter" in keys

    assert "expert_review_categories" in data
    expert_keys = [item["key"] for item in data["expert_review_categories"]]
    assert "health_wellness_claims" in expert_keys
