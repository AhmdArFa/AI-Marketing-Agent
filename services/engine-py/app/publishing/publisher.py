"""Publishing pipeline: the last mile, approval gated and honest about state.

Channels:
  - file_export: writes the post package (text, image, metadata) to a folder.
    Always available; this is the package a human or another tool posts from.
  - webhook: POSTs the package JSON to PUBLISH_WEBHOOK_URL (a website CMS,
    a scheduler like Buffer or Make, or an internal endpoint).
  - meta: posts photo plus caption to a Facebook Page through the Graph API
    when META_PAGE_ID and META_ACCESS_TOKEN are configured.

No channel pretends: missing configuration returns queued_missing_credentials,
an HTTP failure returns failed with the provider's status, and nothing runs
at all without an explicit approved flag from the orchestrator's human gate.
"""

import base64
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "company"


def publish_package(
    company: str,
    post: Dict[str, Any],
    image_png: Optional[bytes],
    channel: str = "file_export",
    approved: bool = False,
) -> Dict[str, Any]:
    if not approved:
        return {"status": "rejected_not_approved", "channel": channel,
                "detail": "Publishing requires a human approval decision first"}

    stamp = time.strftime("%Y%m%d-%H%M%S")
    package_id = f"{_slug(company)}-{post.get('id', 'post')}-{stamp}"
    body = post.get("variants", {}).get("facebook") or post.get("body", "")

    if channel == "file_export":
        out_dir = Path(os.getenv("PUBLISH_EXPORT_DIR", "outputs")) / package_id
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "post.txt").write_text(body, encoding="utf-8")
        (out_dir / "variants.json").write_text(
            json.dumps(post.get("variants", {}), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if image_png:
            (out_dir / "image.png").write_bytes(image_png)
        (out_dir / "meta.json").write_text(
            json.dumps({"company": company, "package_id": package_id, "pillar": post.get("pillar")},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {"status": "published", "channel": channel, "package_id": package_id,
                "location": str(out_dir), "files": sorted(p.name for p in out_dir.iterdir())}

    if channel == "webhook":
        url = os.getenv("PUBLISH_WEBHOOK_URL", "").strip()
        if not url:
            return {"status": "queued_missing_credentials", "channel": channel,
                    "detail": "Set PUBLISH_WEBHOOK_URL to the receiving website or scheduler endpoint"}
        payload = {
            "company": company,
            "package_id": package_id,
            "text": body,
            "variants": post.get("variants", {}),
            "image_base64": base64.b64encode(image_png).decode() if image_png else None,
        }
        try:
            r = httpx.post(url, json=payload, timeout=10)
            if 200 <= r.status_code < 300:
                return {"status": "published", "channel": channel, "package_id": package_id,
                        "provider_status": r.status_code}
            return {"status": "failed", "channel": channel, "provider_status": r.status_code,
                    "detail": r.text[:200]}
        except Exception as exc:
            return {"status": "failed", "channel": channel, "detail": str(exc)[:200]}

    if channel == "meta":
        page_id = os.getenv("META_PAGE_ID", "").strip()
        token = os.getenv("META_ACCESS_TOKEN", "").strip()
        if not page_id or not token:
            return {"status": "queued_missing_credentials", "channel": channel,
                    "detail": "Set META_PAGE_ID and META_ACCESS_TOKEN for the target Facebook Page"}
        try:
            files = {"source": ("image.png", image_png or b"", "image/png")}
            r = httpx.post(
                f"https://graph.facebook.com/v21.0/{page_id}/photos",
                data={"message": body, "access_token": token},
                files=files,
                timeout=20,
            )
            if 200 <= r.status_code < 300:
                return {"status": "published", "channel": channel, "package_id": package_id,
                        "provider_response": r.json()}
            return {"status": "failed", "channel": channel, "provider_status": r.status_code,
                    "detail": r.text[:200]}
        except Exception as exc:
            return {"status": "failed", "channel": channel, "detail": str(exc)[:200]}

    return {"status": "failed", "channel": channel, "detail": f"Unknown channel: {channel}"}
