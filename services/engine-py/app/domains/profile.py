"""Domain Profile: everything the agent needs to market ANY company.

The agent is domain agnostic. Whoever runs it describes their company once
in a profile (JSON), and generation, branding, and publishing all read from
that profile only. No company, industry, or fact is baked into the engine.

Profile shape (see docs/DOMAIN_PROFILE.md and the shipped examples):

{
  "company_name": "Vo Technology",            # required
  "product_name": "4S PLUS",
  "industry": "Automotive ERP software",
  "tagline": {"en": "...", "ar": "..."},       # string or per language dict
  "key_facts": {"en": ["..."], "ar": ["..."]},
  "value_props": {"en": ["..."], "ar": ["..."]},
  "audiences": [{"name": "...", "kind": "prospecting",
                 "pains": {"en": ["..."], "ar": ["..."]}}],
  "pillars": [{"name": "...", "angle": "..."}],
  "ctas": {"en": ["Book a live demo."], "ar": ["..."]},
  "hashtags": ["#AutoERP"],
  "brand": {"bg": "#14181d", "accent": "#f59e0b", "text": "#f0f4f8",
            "muted": "#a0acbc", "logo_path": null}
}
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

DEFAULT_BRAND = {"bg": "#14181d", "accent": "#f59e0b", "text": "#f0f4f8", "muted": "#a0acbc"}


def hex_to_rgb(value: str) -> tuple:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _lang_map(value: Any) -> Dict[str, List[str]]:
    """Normalize string | list | {lang: list} into {lang: [items]}."""
    if value is None:
        return {}
    if isinstance(value, str):
        return {"en": [value], "ar": [value]}
    if isinstance(value, list):
        return {"en": [str(v) for v in value], "ar": [str(v) for v in value]}
    if isinstance(value, dict):
        return {k: [str(x) for x in (v if isinstance(v, list) else [v])] for k, v in value.items()}
    return {}


def pick(mapping: Dict[str, List[str]], language: str) -> List[str]:
    if not mapping:
        return []
    if language in mapping:
        return mapping[language]
    return mapping.get("en") or next(iter(mapping.values()))


@dataclass
class DomainProfile:
    company_name: str
    product_name: str = ""
    industry: str = ""
    tagline: Dict[str, List[str]] = field(default_factory=dict)
    key_facts: Dict[str, List[str]] = field(default_factory=dict)
    value_props: Dict[str, List[str]] = field(default_factory=dict)
    audiences: List[Dict[str, Any]] = field(default_factory=list)
    pillars: List[Dict[str, Any]] = field(default_factory=list)
    ctas: Dict[str, List[str]] = field(default_factory=dict)
    hashtags: List[str] = field(default_factory=list)
    brand: Dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_BRAND))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainProfile":
        if not isinstance(data, dict):
            raise ValueError("Domain profile must be a JSON object")
        company = str(data.get("company_name", "")).strip()
        if not company:
            raise ValueError("Domain profile is missing the required field: company_name")
        brand = dict(DEFAULT_BRAND)
        for key, value in (data.get("brand") or {}).items():
            if key in ("bg", "accent", "text", "muted"):
                if not isinstance(value, str) or not _HEX.match(value):
                    raise ValueError(f"brand.{key} must be a hex color like #f59e0b, got {value!r}")
                brand[key] = value
            elif key == "logo_path":
                brand[key] = value
        audiences = []
        for aud in data.get("audiences") or []:
            audiences.append(
                {
                    "name": aud.get("name", "Audience"),
                    "kind": aud.get("kind", "prospecting"),
                    "pains": _lang_map(aud.get("pains")),
                }
            )
        return cls(
            company_name=company,
            product_name=str(data.get("product_name", "")),
            industry=str(data.get("industry", "")),
            tagline=_lang_map(data.get("tagline")),
            key_facts=_lang_map(data.get("key_facts")),
            value_props=_lang_map(data.get("value_props")),
            audiences=audiences,
            pillars=[{"name": p.get("name", ""), "angle": p.get("angle", "")} for p in data.get("pillars") or []],
            ctas=_lang_map(data.get("ctas")),
            hashtags=[str(h) for h in data.get("hashtags") or []],
            brand=brand,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "DomainProfile":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def facts(self, language: str) -> List[str]:
        return pick(self.key_facts, language)

    def props(self, language: str) -> List[str]:
        return pick(self.value_props, language)

    def cta(self, language: str) -> str:
        options = pick(self.ctas, language)
        if options:
            return options[0]
        return "Book a live demo." if language == "en" else "احجز عرض حي."

    def tagline_text(self, language: str) -> str:
        options = pick(self.tagline, language)
        return options[0] if options else self.industry

    def palette(self) -> Dict[str, tuple]:
        return {k: hex_to_rgb(self.brand[k]) for k in ("bg", "accent", "text", "muted")}
