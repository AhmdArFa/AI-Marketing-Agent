import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
import io

from app.domains.profile import DomainProfile
from app.generation.copywriter import generate_from_profile
from app.generation.creative import render_image
from app.main import app

client = TestClient(app)
ENGINE_DIR = Path(__file__).resolve().parent.parent
DENTAL = json.loads((ENGINE_DIR / "examples" / "nile_dental_clinic.json").read_text(encoding="utf-8"))


def test_generic_profile_generates_its_own_domain_copy():
    profile = DomainProfile.from_dict(DENTAL)
    out = generate_from_profile(profile, audience="customers", language="en", count=3)
    assert len(out["posts"]) == 3
    joined = " ".join(p["body"] for p in out["posts"])
    assert "Nile Dental" in joined or "Nile Dental Clinic" in joined
    # The clinic's own facts show up; nothing from the automotive profile leaks in
    assert "autoclave" in joined.lower() or "anesthesia" in joined.lower()
    for banned in ("JobCard", "chassis", "workshop"):
        assert banned not in joined
    assert out["all_guardrail_ok"] is True


def test_generic_profile_arabic():
    profile = DomainProfile.from_dict(DENTAL)
    out = generate_from_profile(profile, audience="customers", language="ar", count=2)
    joined = " ".join(p["body"] for p in out["posts"])
    assert "التعقيم" in joined or "خايف" in joined or "علاج" in joined
    assert out["all_guardrail_ok"] is True


def test_brand_palette_applies_to_image():
    profile = DomainProfile.from_dict(DENTAL)
    png = render_image(
        profile.company_name, profile.product_name, "No Fear Visits", "Dentistry without fear",
        palette=DENTAL["brand"],
    )
    img = Image.open(io.BytesIO(png)).convert("RGB")
    assert img.getpixel((10, 7)) == (45, 212, 191)  # teal accent top stripe
    assert img.getpixel((500, 500)) == (6, 42, 48)  # clinic bg, not automotive charcoal


def test_profile_validation():
    with pytest.raises(ValueError):
        DomainProfile.from_dict({"product_name": "X"})
    bad = dict(DENTAL)
    bad["brand"] = {"accent": "teal"}
    with pytest.raises(ValueError):
        DomainProfile.from_dict(bad)


def test_api_accepts_full_profile():
    r = client.post(
        "/v1/generate/campaign",
        json={"profile": DENTAL, "language": "en", "audience": "customers", "count": 2},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["company"] == "Nile Dental Clinic"
    assert "bg=%23062a30" in body["posts"][0]["image_url"]
    bad = client.post("/v1/generate/campaign", json={"profile": {"product_name": "X"}})
    assert bad.status_code == 422


def test_cli_runs_like_a_user_would(tmp_path):
    proc = subprocess.run(
        [
            sys.executable, "run_campaign.py",
            "--profile", "examples/nile_dental_clinic.json",
            "--language", "en", "--audience", "customers", "--count", "2",
            "--approve", "--out", str(tmp_path),
        ],
        cwd=ENGINE_DIR, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-500:]
    assert "Guardrails clean on all posts: True" in proc.stdout
    packages = list(tmp_path.glob("nile-dental-clinic-post-*"))
    assert len(packages) == 2
    assert (packages[0] / "image.png").exists() and (packages[0] / "post.txt").exists()
