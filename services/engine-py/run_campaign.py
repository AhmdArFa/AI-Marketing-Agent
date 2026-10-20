"""Run the marketing agent from the command line, on your own machine.

    python run_campaign.py --profile examples/vo_technology_4splus.json
    python run_campaign.py --profile examples/nile_dental_clinic.json \
        --language ar --audience customers --count 4
    python run_campaign.py --profile my_company.json --channel webhook

Without --approve the packages are generated and printed as drafts only.
With --approve they are pushed through the chosen channel (file_export by
default; webhook and meta read their endpoints and tokens from the
environment, see docs/DOMAIN_PROFILE.md).
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.domains.profile import DomainProfile
from app.generation.copywriter import generate_from_profile
from app.generation.creative import render_image
from app.publishing.publisher import publish_package


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and optionally publish a marketing campaign for any domain profile")
    parser.add_argument("--profile", required=True, help="Path to the domain profile JSON")
    parser.add_argument("--language", default="en", choices=["en", "ar"])
    parser.add_argument("--audience", default="prospecting", choices=["prospecting", "customers"],
                        help="prospecting: sell the product to businesses. customers: market to end customers")
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--channel", default="file_export", choices=["file_export", "webhook", "meta"])
    parser.add_argument("--out", default="outputs", help="Export folder for the file_export channel")
    parser.add_argument("--approve", action="store_true", help="Push the packages through the channel after generation")
    args = parser.parse_args()

    profile = DomainProfile.from_file(args.profile)
    engine_audience = "prospecting" if args.audience == "prospecting" else "dealer_marketing"
    campaign = generate_from_profile(
        profile, audience=engine_audience, language=args.language, count=args.count
    )
    print(f"Company: {campaign['company']} | Product: {campaign['product']} | Posts: {len(campaign['posts'])}")
    print(f"Guardrails clean on all posts: {campaign['all_guardrail_ok']}")

    os.environ.setdefault("PUBLISH_EXPORT_DIR", args.out)
    for post in campaign["posts"]:
        print(f"\n--- {post['id']} | {post['pillar']} | {post['status']} ---")
        print(post["body"])
        if not args.approve:
            continue
        img = post["image"]
        png = render_image(
            profile.company_name,
            profile.product_name,
            img["headline"],
            img["subline"],
            palette=img.get("brand"),
        )
        result = publish_package(
            profile.company_name, post, png, channel=args.channel, approved=True
        )
        print(f"PUBLISH {result['status']} via {result['channel']}: {result.get('location') or result.get('detail') or result.get('package_id')}")
    if not args.approve:
        print("\nDrafts only. Re run with --approve to push them through the channel.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
