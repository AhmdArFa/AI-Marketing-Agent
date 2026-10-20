"""Copywriter: turns a Domain Profile into real marketing posts.

Domain agnostic by design: every word of substance (facts, value props,
audience pains, CTAs, hashtags) comes from the caller's Domain Profile.
The engine contributes structure: four post patterns per language, seeded
rotation so the same profile produces a varied campaign, channel variants,
and a claim guardrail pass on every single post before it leaves.
"""

import hashlib
from typing import Any, Dict, List

from ..domains.profile import DomainProfile
from ..domain4s.guardrails import check_draft

# The bundled example profile: Vo Technology / 4S PLUS. It is data, not
# engine logic; any other company ships its own profile the same way.
BUNDLED_4SPLUS_PROFILE: Dict[str, Any] = {
    "company_name": "Vo Technology",
    "product_name": "4S PLUS",
    "industry": "Automotive ERP software",
    "tagline": {
        "en": "Sales, Spare Parts, Service and Survey in one system",
        "ar": "المبيعات وقطع الغيار والصيانة وتقييم العملاء في نظام واحد",
    },
    "key_facts": {
        "en": [
            "A car sold in Sales carries its chassis history into Service, its parts requests into the warehouse, its invoice into Accounting, and its survey back into CRM.",
            "Every JobCard tracks actual hours versus sold hours, from W.I.P to Ready for invoicing.",
            "A JobCard raises a Create Request, Spare Parts confirms, and the issue drops stock instantly.",
            "The system watches months and kilometres per car and reminds owners when periodic maintenance is due.",
        ],
        "ar": [
            "العربية اللي اتباعت في المبيعات بتكمل برقم الشاسيه بتاعها في الصيانة، وقطع غيارها بتتطلب من المخزن، وفاتورتها بتروح المحاسبة، وتقييم العميل بيرجع لإدارة العملاء.",
            "كل كرت شغل بيتابع الساعات الفعلية قدام الساعات المباعة، من بداية الشغل لحد جاهز للفوترة.",
            "كرت الشغل بيعمل طلب قطع غيار، وقطع الغيار بتأكد، والصرف بيخصم من المخزون في لحظتها.",
            "النظام بيراقب الشهور والكيلومترات لكل عربية وبيفكر العميل لما معاد الصيانة الدورية يقرب.",
        ],
    },
    "value_props": {
        "en": [
            "No retyping and no lost history between departments.",
            "Know the profit on every JobCard, not just at month end.",
            "Technicians never wait on a paper request again.",
        ],
        "ar": [
            "من غير إعادة إدخال ومن غير ما تاريخ العربية يضيع بين الأقسام.",
            "اعرف ربح كل كرت شغل، مش بس آخر الشهر.",
            "الفني مش هيستنى طلب ورقي تاني.",
        ],
    },
    "audiences": [
        {
            "name": "Dealer or workshop owner",
            "kind": "prospecting",
            "pains": {
                "en": ["running your workshop on paper job cards and memory"],
                "ar": ["مدير مركزك بكرت شغل ورقي وبالذاكرة"],
            },
        },
        {
            "name": "Car owner",
            "kind": "customers",
            "pains": {
                "en": ["forgetting your service intervals until wear becomes a repair"],
                "ar": ["ناسي معاد صيانتك لحد ما الاستهلاك يبقى إصلاح كبير"],
            },
        },
    ],
    "pillars": [
        {"name": "One Car Journey", "angle": "One car, one story, from sale to survey"},
        {"name": "Workshop Profit", "angle": "Actual versus sold hours decide workshop profit"},
        {"name": "Retention on Schedule", "angle": "A reminder at the right kilometre is retention you can schedule"},
    ],
    "ctas": {"en": ["Book a live demo on your own data."], "ar": ["احجز عرض حي على بياناتك."]},
    "hashtags": ["#AutoERP", "#WorkshopManagement", "#4SPLUS", "#Dealership"],
    "brand": {"bg": "#14181d", "accent": "#f59e0b", "text": "#f0f4f8", "muted": "#a0acbc"},
}

PATTERNS = {
    "en": [
        "{fact} This is how {product} works at {company}. {cta}",
        "Still {pain}? {prop} That is {product} by {company}. {cta}",
        "{prop} {fact} {brand} {cta}",
        "{angle}. {fact} {cta}",
    ],
    "ar": [
        "{fact} ده أسلوب {product} من {company}. {cta}",
        "لسه {pain}؟ {prop} ده {product} من {company}. {cta}",
        "{prop} {fact} {brand} {cta}",
        "{angle}. {fact} {cta}",
    ],
}


def _rotate(items: List[str], seed: str, offset: int = 0) -> List[str]:
    if not items:
        return []
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    start = (digest[0] + offset) % len(items)
    return items[start:] + items[:start]


def _audience_pains(profile: DomainProfile, audience: str, language: str) -> List[str]:
    kinds = {"prospecting"} if audience == "prospecting" else {"customers", "dealer_marketing"}
    pains: List[str] = []
    for aud in profile.audiences:
        if aud["kind"] in kinds:
            from ..domains.profile import pick

            pains.extend(pick(aud["pains"], language))
    return pains


def generate_from_profile(
    profile: DomainProfile,
    audience: str = "prospecting",
    language: str = "en",
    count: int = 3,
) -> Dict[str, Any]:
    facts = profile.facts(language) or [profile.tagline_text(language) or profile.industry]
    props = profile.props(language) or facts
    pains = _audience_pains(profile, audience, language)
    patterns = PATTERNS.get(language, PATTERNS["en"])
    seed = f"{profile.company_name}:{language}:{audience}"
    facts_r = _rotate(facts, seed, 0)
    props_r = _rotate(props, seed, 1)
    pains_r = _rotate(pains, seed, 2)
    pillars = profile.pillars or [{"name": profile.industry or "Value", "angle": profile.tagline_text(language)}]
    cta = profile.cta(language)
    tags = profile.hashtags or [f"#{profile.company_name.replace(' ', '')}"]

    posts: List[Dict[str, Any]] = []
    total = max(1, min(count, 12))
    for i in range(total):
        fact = facts_r[i % len(facts_r)]
        prop = props_r[i % len(props_r)]
        pain = pains_r[i % len(pains_r)] if pains_r else prop
        pillar = pillars[i % len(pillars)]
        angle = pillar.get("angle") or profile.tagline_text(language)
        pattern = patterns[i % len(patterns)]
        if "{pain}" in pattern and not pains_r:
            pattern = patterns[2]
        product_label = profile.product_name or profile.company_name
        brand_line = (
            f"Built by {profile.company_name}, inside {product_label}."
            if language == "en"
            else f"من تطوير {profile.company_name}، جوه {product_label}."
        )
        body = pattern.format(
            fact=fact, prop=prop, pain=pain, angle=angle, brand=brand_line,
            product=product_label,
            company=profile.company_name, cta=cta,
        )
        body = " ".join(body.split())
        guard = check_draft(body)
        short = body if len(body) <= 260 else body[:257].rsplit(" ", 1)[0] + "..."
        headline = pillar.get("name") or prop.split(".")[0][:48]
        posts.append(
            {
                "id": f"post-{i + 1}",
                "pillar": pillar.get("name", ""),
                "body": body,
                "variants": {
                    "linkedin": body + "\n\n" + " ".join(tags),
                    "facebook": body,
                    "x": short,
                    "instagram": body + "\n\n" + " ".join(tags),
                },
                "hashtags": tags,
                "image": {
                    "headline": headline,
                    "subline": profile.tagline_text(language),
                    "theme": "profile",
                    "brand": dict(profile.brand),
                },
                "guardrail_ok": guard["ok"],
                "status": "draft_ready" if guard["ok"] else "blocked_by_guardrails",
            }
        )
    return {
        "company": profile.company_name,
        "product": profile.product_name,
        "industry": profile.industry,
        "audience": audience,
        "language": language,
        "posts": posts,
        "all_guardrail_ok": all(p["guardrail_ok"] for p in posts),
    }


def generate_campaign(
    company_name: str,
    product_name: str = "4S PLUS",
    domain: str = "automotive_erp",
    audience: str = "prospecting",
    language: str = "en",
    count: int = 3,
) -> Dict[str, Any]:
    """Backward compatible entry point on the bundled 4S PLUS profile."""
    data = dict(BUNDLED_4SPLUS_PROFILE)
    data["company_name"] = company_name
    data["product_name"] = product_name
    profile = DomainProfile.from_dict(data)
    result = generate_from_profile(profile, audience=audience, language=language, count=count)
    result["domain"] = domain
    return result
