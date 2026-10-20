"""Copywriter: turns (company, product, domain, audience) into real posts.

Deterministic template engine seeded with verified domain facts, so output
is real publishable copy today, in Arabic and English, and every draft is
passed through the claim guardrails before it leaves. When a live LLM
provider is configured, its copy can replace the template body behind this
same interface; the guardrail gate stays either way.
"""

import hashlib
from typing import Any, Dict, List

from ..domain4s.guardrails import check_draft

TEMPLATES_EN_PROSPECTING = [
    {
        "pillar": "One Car Journey",
        "body": "One car, one story. With {product} by {company}, a car sold in Sales carries its chassis history into Service, its parts requests into the warehouse, its invoice into Accounting, and its survey back into CRM. No retyping, no lost history. Book a live demo on your own data.",
        "headline": "One Car. One Journey.",
        "subline": "Sales to Service to Survey, in {product}",
    },
    {
        "pillar": "Workflow Relief",
        "body": "Paper job cards hide the two numbers that decide a workshop's profit: actual hours versus sold hours. {product} by {company} tracks both on every JobCard, from W.I.P to Ready for invoicing. See your workshop the way it really runs. Book a live demo.",
        "headline": "Actual vs Sold Hours",
        "subline": "Know the profit on every JobCard",
    },
    {
        "pillar": "Education",
        "body": "A service reminder is not spam when it arrives at the right kilometre. Dealers on {product} let the system watch months and kilometres per car and remind owners before small wear becomes a big repair. That is retention you can schedule. Ask {company} how it works.",
        "headline": "Reminders That Arrive on Time",
        "subline": "Maintenance due, detected automatically",
    },
    {
        "pillar": "Pain Point",
        "body": "Parts requested on paper get lost. In {product}, the JobCard raises a Create Request, Spare Parts confirms, and the issue drops stock instantly. The technician never waits on a guess. Book a live demo on your own data.",
        "headline": "No More Lost Parts Requests",
        "subline": "JobCard to warehouse in one flow",
    },
]

TEMPLATES_AR_PROSPECTING = [
    {
        "pillar": "رحلة عربية واحدة",
        "body": "عربية واحدة، قصة واحدة. مع {product} من {company}، العربية اللي اتباعت في المبيعات بتكمل برقم الشاسيه بتاعها في الصيانة، وقطع غيارها بتتطلب من المخزن، وفاتورتها بتروح المحاسبة، وتقييم العميل بيرجع لإدارة العملاء. من غير إعادة إدخال ومن غير ما التاريخ يضيع. احجز عرض حي على بياناتك.",
        "headline": "عربية واحدة. رحلة واحدة.",
        "subline": "من البيع للصيانة لتقييم العميل في {product}",
    },
    {
        "pillar": "تخفيف الشغل اليدوي",
        "body": "كروت الشغل الورقية بتخبي أهم رقمين في ربح أي مركز صيانة: الساعات الفعلية والساعات المباعة. {product} من {company} بيتابع الرقمين على كل كرت شغل، من بداية الشغل لحد جاهز للفوترة. شوف مركزك على حقيقته. احجز عرض حي.",
        "headline": "الفعلي قدام المباع",
        "subline": "اعرف ربح كل كرت شغل بدقة",
    },
    {
        "pillar": "توعية",
        "body": "تنبيه الصيانة مش إزعاج لو وصل في الكيلومتر الصح. الموزعين على {product} بيخلوا النظام يراقب الشهور والكيلومترات لكل عربية ويفكر العميل قبل ما الاستهلاك البسيط يبقى إصلاح كبير. ده احتفاظ بالعملاء يتعمل بجدول. اسأل {company} بيشتغل ازاي.",
        "headline": "تنبيهات بتوصل في وقتها",
        "subline": "الصيانة الدورية بتتكشف تلقائيا",
    },
    {
        "pillar": "نقطة ألم",
        "body": "طلبات قطع الغيار الورقية بتضيع. في {product}، كرت الشغل بيعمل طلب، وقطع الغيار بتأكد، والصرف بيخصم من المخزون في لحظتها. الفني مش بيستنى تخمين. احجز عرض حي على بياناتك.",
        "headline": "طلبات قطع الغيار مش بتضيع",
        "subline": "من كرت الشغل للمخزن في خطوة واحدة",
    },
]

TEMPLATES_EN_DEALER = [
    {
        "pillar": "Retention",
        "body": "Your next service is due, and your car's full history is already with us. Book your periodic maintenance today and keep the record that protects your resale value. One visit, everything on file.",
        "headline": "Your Service Is Due",
        "subline": "Full history kept with your car",
    },
    {
        "pillar": "Trust",
        "body": "After every visit we ask one question: how did we do? Your score decides what happens next, and low scores get a human call, not an automated message. Your voice runs this workshop.",
        "headline": "Your Score Decides",
        "subline": "Real follow up after every visit",
    },
]

TEMPLATES_AR_DEALER = [
    {
        "pillar": "احتفاظ بالعملاء",
        "body": "صيانتك الدورية معادها قرب، وتاريخ عربيتك كله محفوظ عندنا. احجز صيانتك النهاردة وحافظ على السجل اللي بيحمي قيمة عربيتك عند إعادة البيع. زيارة واحدة وكل حاجة متسجلة.",
        "headline": "معاد صيانتك قرب",
        "subline": "تاريخ عربيتك محفوظ بالكامل",
    },
    {
        "pillar": "ثقة",
        "body": "بعد كل زيارة بنسألك سؤال واحد: خدمتنا كانت عاملة ازاي؟ تقييمك هو اللي بيقرر الخطوة الجاية، والتقييمات القليلة بتاخد مكالمة من إنسان، مش رسالة آلية. صوتك هو اللي بيدير المركز.",
        "headline": "تقييمك هو اللي بيقرر",
        "subline": "متابعة حقيقية بعد كل زيارة",
    },
]

HASHTAGS = {
    "prospecting": ["#AutoERP", "#WorkshopManagement", "#4SPLUS", "#Dealership", "#AgenticAI"],
    "dealer_marketing": ["#CarService", "#PeriodicMaintenance", "#4SPLUS", "#CustomerCare"],
}


def _seeded_order(items: List[Dict[str, str]], seed_text: str) -> List[Dict[str, str]]:
    digest = hashlib.sha256(seed_text.encode("utf-8")).digest()
    order = sorted(range(len(items)), key=lambda i: digest[i % len(digest)])
    return [items[i] for i in order]


def generate_campaign(
    company_name: str,
    product_name: str = "4S PLUS",
    domain: str = "automotive_erp",
    audience: str = "prospecting",
    language: str = "en",
    count: int = 3,
) -> Dict[str, Any]:
    if language == "ar":
        pool = TEMPLATES_AR_PROSPECTING if audience == "prospecting" else TEMPLATES_AR_DEALER
    else:
        pool = TEMPLATES_EN_PROSPECTING if audience == "prospecting" else TEMPLATES_EN_DEALER
    ordered = _seeded_order(pool, f"{company_name}:{product_name}:{audience}:{language}")
    tags = HASHTAGS.get(audience, HASHTAGS["prospecting"])

    posts: List[Dict[str, Any]] = []
    for idx, tpl in enumerate(ordered[: max(1, min(count, len(ordered)))]):
        body = tpl["body"].format(product=product_name, company=company_name)
        guard = check_draft(body)
        short = body if len(body) <= 260 else body[:257].rsplit(" ", 1)[0] + "..."
        posts.append(
            {
                "id": f"post-{idx + 1}",
                "pillar": tpl["pillar"],
                "body": body,
                "variants": {
                    "linkedin": body + "\n\n" + " ".join(tags),
                    "facebook": body,
                    "x": short,
                    "instagram": body + "\n\n" + " ".join(tags),
                },
                "hashtags": tags,
                "image": {
                    "headline": tpl["headline"],
                    "subline": tpl["subline"].format(product=product_name, company=company_name),
                    "theme": "automotive" if domain == "automotive_erp" else "saas",
                },
                "guardrail_ok": guard["ok"],
                "status": "draft_ready" if guard["ok"] else "blocked_by_guardrails",
            }
        )
    return {
        "company": company_name,
        "product": product_name,
        "domain": domain,
        "audience": audience,
        "language": language,
        "posts": posts,
        "all_guardrail_ok": all(p["guardrail_ok"] for p in posts),
    }
