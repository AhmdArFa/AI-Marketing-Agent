import io

from fastapi.testclient import TestClient
from PIL import Image

from app.brain import Brain
from app.generation.copywriter import generate_campaign
from app.generation.creative import render_image
from app.main import app
from app.publishing.publisher import publish_package

client = TestClient(app)


def test_copywriter_generates_real_posts_with_company_name():
    out = generate_campaign("Vo Technology", "4S PLUS", language="en", count=3)
    assert len(out["posts"]) == 3
    for post in out["posts"]:
        assert "Vo Technology" in post["body"] or "4S PLUS" in post["body"]
        assert post["guardrail_ok"] is True
        assert post["status"] == "draft_ready"
        assert set(post["variants"]) == {"linkedin", "facebook", "x", "instagram"}
        assert len(post["variants"]["x"]) <= 263
    assert out["all_guardrail_ok"] is True


def test_copywriter_arabic():
    out = generate_campaign("فو تكنولوجي", "4S PLUS", language="ar", count=2)
    assert len(out["posts"]) == 2
    assert all(p["guardrail_ok"] for p in out["posts"])
    assert any("صيانة" in p["body"] or "كرت شغل" in p["body"] for p in out["posts"])


def test_creative_renders_real_png():
    png = render_image("Vo Technology", "4S PLUS", "One Car. One Journey.", "Sales to Service to Survey")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    img = Image.open(io.BytesIO(png))
    assert img.size == (1080, 1080)


def test_creative_renders_arabic_headline():
    png = render_image("فو تكنولوجي", "4S PLUS", "عربية واحدة. رحلة واحدة.", "من البيع للصيانة")
    img = Image.open(io.BytesIO(png))
    assert img.size == (1080, 1080)


def test_publish_requires_approval():
    r = client.post(
        "/v1/publish",
        json={"company_name": "Vo Technology", "post": {"id": "post-1", "body": "x"}},
    )
    assert r.status_code == 403


def test_publish_file_export_writes_package(tmp_path, monkeypatch):
    monkeypatch.setenv("PUBLISH_EXPORT_DIR", str(tmp_path))
    post = generate_campaign("Vo Technology", "4S PLUS", count=1)["posts"][0]
    png = render_image("Vo Technology", "4S PLUS", post["image"]["headline"], post["image"]["subline"])
    result = publish_package("Vo Technology", post, png, channel="file_export", approved=True)
    assert result["status"] == "published"
    assert "post.txt" in result["files"] and "image.png" in result["files"]
    location = tmp_path / result["package_id"]
    assert (location / "post.txt").read_text(encoding="utf-8") == post["variants"]["facebook"]


def test_publish_webhook_queues_without_url(monkeypatch):
    monkeypatch.delenv("PUBLISH_WEBHOOK_URL", raising=False)
    post = generate_campaign("Vo Technology", "4S PLUS", count=1)["posts"][0]
    result = publish_package("Vo Technology", post, None, channel="webhook", approved=True)
    assert result["status"] == "queued_missing_credentials"


def test_generate_endpoints_and_brain_skill():
    r = client.post(
        "/v1/generate/campaign",
        json={"company_name": "Vo Technology", "language": "ar", "count": 2},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["posts"]) == 2
    assert body["posts"][0]["image_url"].startswith("/v1/generate/image?")

    img = client.get(body["posts"][0]["image_url"])
    assert img.status_code == 200
    assert img.headers["content-type"] == "image/png"

    brain = Brain()
    out = brain.run(
        "gen-test",
        "Generate posts for this company",
        {"company_name": "Vo Technology", "language": "en", "count": 2},
    )
    assert out["skill_id"] == "campaign_package_generator"
    assert out["pending_approvals"] and out["pending_approvals"][0]["tool"] == "publishing.publish"
    assert out["executed_mutations"] == []
