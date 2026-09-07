from datetime import datetime, timezone, timedelta
from backend.sentiment import analyze_comment


def test_sentiment_scorer_positive():
    res = analyze_comment("Absolutely in love with this product! Highly recommended.")
    assert res["sentiment"] == "positive"
    assert res["sentiment_score"] > 0.05
    assert res["flagged_for_review"] is False


def test_sentiment_scorer_negative_and_crisis():
    res = analyze_comment("This is a total scam. The seller cheated me, product gave me allergy and is fake!")
    assert res["sentiment"] == "negative"
    assert res["sentiment_score"] < -0.05
    assert res["flagged_for_review"] is True
    assert "crisis keyword" in res["explanation"].lower()
    assert "scam" in res["matched_keywords"]
    assert "cheated" in res["matched_keywords"]


def test_sentiment_scorer_neutral():
    res = analyze_comment("The package arrived on Tuesday.")
    assert res["sentiment"] == "neutral"
    assert res["flagged_for_review"] is False


def test_mentions_ingest_unauthorized(client):
    res = client.post("/api/mentions/ingest", json={"post_id": "test_post_1", "comments": [{"text": "cool"}]})
    assert res.status_code == 401


def test_mentions_ingest_success(client, auth_headers):
    payload = {
        "post_id": "ig_post_999",
        "platform": "Instagram",
        "author_handle": "@brand",
        "comments": [
            {"text": "Loving this serum so much!", "author_handle": "@user1"},
            {"text": "Terrible customer service, total fraud.", "author_handle": "@user2"},
            {"text": "Where can I buy this?", "author_handle": "@user3"},
        ]
    }
    res = client.post("/api/mentions/ingest", json=payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert len(data) == 3

    # Check first comment (positive)
    assert data[0]["sentiment"] == "positive"
    assert data[0]["flagged_for_review"] is False

    # Check second comment (negative + flagged for fraud)
    assert data[1]["sentiment"] == "negative"
    assert data[1]["flagged_for_review"] is True
    assert "fraud" in data[1]["explanation"]


def test_mentions_filtering_and_isolation(client, auth_headers):
    # User 1 ingests 2 comments
    client.post("/api/mentions/ingest", json={
        "post_id": "p1",
        "comments": [
            {"text": "Amazing experience!", "author_handle": "@u1"},
            {"text": "Worst experience ever, complete scam!", "author_handle": "@u2"}
        ]
    }, headers=auth_headers)

    # Filter positive
    res_pos = client.get("/api/mentions?sentiment=positive", headers=auth_headers)
    assert res_pos.status_code == 200
    assert len(res_pos.json()) == 1
    assert res_pos.json()[0]["sentiment"] == "positive"

    # Filter flagged only
    res_flag = client.get("/api/mentions?flagged_only=true", headers=auth_headers)
    assert res_flag.status_code == 200
    assert len(res_flag.json()) == 1
    assert res_flag.json()[0]["flagged_for_review"] is True

    # User 2 logs in -> should see 0 mentions (tenant isolation)
    client.post("/api/auth/signup", json={"email": "otheruser@example.com", "password": "password123"})
    login_res = client.post(
        "/api/auth/login",
        data={"username": "otheruser@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    user2_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    res_u2 = client.get("/api/mentions", headers=user2_headers)
    assert res_u2.status_code == 200
    assert len(res_u2.json()) == 0


def test_mentions_summary_and_anomaly_detection(client, auth_headers):
    now = datetime.now(timezone.utc)

    # Seed trailing 7 days with 1 negative mention per day
    comments_history = []
    for i in range(1, 8):
        day_date = now - timedelta(days=i)
        comments_history.append({
            "text": "Not satisfied with this product.",
            "author_handle": f"@u_day_{i}",
            "detected_at": day_date.isoformat()
        })

    # Today: Ingest 4 negative mentions (>= 2x trailing average of 1.0)
    for i in range(4):
        comments_history.append({
            "text": "Complete scam, broken on arrival, total fraud!",
            "author_handle": f"@u_today_{i}",
            "detected_at": now.isoformat()
        })

    # Also 2 positive mentions
    comments_history.append({"text": "I like the color!", "author_handle": "@u_pos1", "detected_at": now.isoformat()})
    comments_history.append({"text": "Great and fast shipping!", "author_handle": "@u_pos2", "detected_at": now.isoformat()})

    client.post("/api/mentions/ingest", json={"post_id": "trend_post", "comments": comments_history}, headers=auth_headers)

    res = client.get("/api/mentions/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_mentions"] == len(comments_history)
    assert data["positive_count"] == 2
    assert data["negative_count"] == 11
    assert data["flagged_count"] >= 4

    # Check Anomaly Report: 4 negative comments today vs 1.0 trailing average -> Anomaly triggered!
    anomaly = data["anomaly"]
    assert anomaly["is_anomalous"] is True
    assert anomaly["current_daily_negative"] == 4
    assert anomaly["trailing_7day_avg"] == 1.0
    assert "Reputation Alert" in anomaly["explanation"]


def test_sentiment_multilingual_routing():
    # 1. Hindi Devanagari Script
    devanagari_text = "यह उत्पाद बहुत घटिया है और पैसे बर्बाद हो गए।"
    res_indic = analyze_comment(devanagari_text)
    assert res_indic["language"] == "indic"
    assert res_indic["sentiment"] in ["needs_review", "negative"]

    # 2. Hinglish Code-Mixed
    hinglish_text = "Bhai bilkul bekaar service hai, customer care wale chor hain"
    res_hinglish = analyze_comment(hinglish_text)
    assert res_hinglish["language"] == "hinglish"
    assert res_hinglish["sentiment"] in ["needs_review", "negative"]


def test_mentions_language_filtering_and_needs_review(client, auth_headers):
    payload = {
        "post_id": "lang_test_post",
        "comments": [
            {"text": "Love the product, fantastic quality!", "author_handle": "@eng_user"},
            {"text": "Bhai ekdum bekaar hai, paisa barbaad", "author_handle": "@hinglish_user"},
            {"text": "यह उत्पाद बहुत खराब है", "author_handle": "@hindi_user"},
        ]
    }
    ingest_res = client.post("/api/mentions/ingest", json=payload, headers=auth_headers)
    assert ingest_res.status_code == 201
    data = ingest_res.json()
    assert len(data) == 3

    # Check languages assigned
    langs = {d["author_handle"]: d["language"] for d in data}
    assert langs["@eng_user"] == "en"
    assert langs["@hinglish_user"] == "hinglish"
    assert langs["@hindi_user"] == "indic"

    # Filter by Hinglish
    res_hi = client.get("/api/mentions?language=hinglish", headers=auth_headers)
    assert res_hi.status_code == 200
    assert len(res_hi.json()) >= 1
    assert all(m["language"] == "hinglish" for m in res_hi.json())

    # Filter by Indic
    res_indic = client.get("/api/mentions?language=indic", headers=auth_headers)
    assert res_indic.status_code == 200
    assert len(res_indic.json()) >= 1
    assert all(m["language"] == "indic" for m in res_indic.json())

    # Check Summary includes needs_review_count
    res_sum = client.get("/api/mentions/summary", headers=auth_headers)
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert "needs_review_count" in sum_data
    assert sum_data["needs_review_count"] >= 0


def test_mentions_retention_cleanup(client, auth_headers):
    now = datetime.now(timezone.utc)
    old_date = now - timedelta(days=95)
    recent_date = now - timedelta(days=10)

    payload = {
        "post_id": "retention_test_post",
        "comments": [
            {"text": "Very old comment from 95 days ago", "author_handle": "@old_user", "detected_at": old_date.isoformat()},
            {"text": "Recent comment from 10 days ago", "author_handle": "@recent_user", "detected_at": recent_date.isoformat()},
        ]
    }
    client.post("/api/mentions/ingest", json=payload, headers=auth_headers)

    # Trigger cleanup with 90-day retention
    cleanup_res = client.post("/api/mentions/cleanup", json={"days_retention": 90}, headers=auth_headers)
    assert cleanup_res.status_code == 200
    res_data = cleanup_res.json()
    assert res_data["deleted_count"] >= 1
    assert res_data["retention_days"] == 90
    assert res_data["status"] == "COMPLETED"

    # Verify old comment was removed, recent remains
    list_res = client.get("/api/mentions?post_id=retention_test_post", headers=auth_headers)
    remaining_authors = [m["author_handle"] for m in list_res.json()]
    assert "@recent_user" in remaining_authors
    assert "@old_user" not in remaining_authors

