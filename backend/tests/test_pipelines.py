from unittest.mock import patch
from core.models import UnifiedAuditReport


def test_link_audit_unauthorized(client):
    res = client.post("/api/audits/link", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert res.status_code == 401


def test_link_audit_empty_url(client, auth_headers):
    res = client.post("/api/audits/link", json={"url": ""}, headers=auth_headers)
    assert res.status_code == 400
    assert "cannot be empty" in res.json()["detail"]


def test_link_audit_unsupported_domain(client, auth_headers):
    res = client.post("/api/audits/link", json={"url": "https://example.com/post/123"}, headers=auth_headers)
    assert res.status_code == 400
    assert "Unsupported URL" in res.json()["detail"]


def test_link_audit_youtube_success_mocked(client, auth_headers):
    mock_report = UnifiedAuditReport(
        post_id="test_vid_123",
        influencer_handle="Tech Channel",
        post_url="https://www.youtube.com/watch?v=test_vid_123",
        timestamp="2026-09-01T12:00:00Z",
        caption_status="COMPLIANT",
        caption_flags=[],
        visual_status="NO_MEDIA",
        visual_flags=[],
        is_compliant=True,
        risk_level="LOW",
        expert_review_flags=[],
    )

    with patch("backend.routers.pipelines.fetch_single_yt_video", return_value=mock_report):
        res = client.post(
            "/api/audits/link",
            json={
                "url": "https://www.youtube.com/watch?v=test_vid_123",
                "yt_api_key": "dummy_key_for_test",
            },
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["platform"] == "YouTube"
        assert data["status"] == "COMPLIANT"
        assert data["is_compliant"] is True
        assert data["influencer_handle"] == "Tech Channel"
        assert "id" in data


def test_account_audit_youtube_success_mocked(client, auth_headers):
    mock_reports = [
        UnifiedAuditReport(
            post_id="v1",
            influencer_handle="@tech",
            post_url="https://youtube.com/watch?v=v1",
            timestamp="2026-09-01",
            caption_status="COMPLIANT",
            caption_flags=[],
            visual_status="DISCLOSURE_VISIBLE",
            visual_flags=["#ad"],
            is_compliant=True,
        ),
        UnifiedAuditReport(
            post_id="v2",
            influencer_handle="@tech",
            post_url="https://youtube.com/watch?v=v2",
            timestamp="2026-09-02",
            caption_status="FLAGGED",
            caption_flags=["approved_label"],
            visual_status="NO_MEDIA",
            visual_flags=[],
            is_compliant=False,
            risk_level="HIGH"
        )
    ]

    with patch("backend.routers.pipelines.run_yt_pipeline", return_value=("@tech", mock_reports)):
        res = client.post(
            "/api/audits/account",
            json={
                "account_url": "https://www.youtube.com/@tech",
                "limit": 5,
                "yt_api_key": "dummy_key"
            },
            headers=auth_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["platform"] == "YouTube"
        assert data["total_audited"] == 2
        assert data["compliant_count"] == 1
        assert data["flagged_count"] == 1
        assert data["health_score"] == 50.0
        assert len(data["posts"]) == 2
