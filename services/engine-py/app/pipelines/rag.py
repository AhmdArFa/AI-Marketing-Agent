"""Dependency light TF IDF retrieval behind a vector store interface.

Swap TfidfRetriever for Chroma (dev) or pgvector (prod) without touching
callers: both must expose add_document and search with the same shapes.
"""

import math
import re
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

_TOKEN = re.compile(r"[a-z0-9\u0600-\u06FF]+", re.IGNORECASE)


def _tokens(text: str) -> List[str]:
    return _TOKEN.findall(text.lower())


class TfidfRetriever:
    def __init__(self) -> None:
        self._docs: Dict[str, str] = {}
        self._tf: Dict[str, Counter] = {}
        self._df: Counter = Counter()

    def add_document(self, doc_id: str, text: str) -> None:
        if doc_id in self._docs:
            for term in set(self._tf[doc_id]):
                self._df[term] -= 1
        counts = Counter(_tokens(text))
        self._docs[doc_id] = text
        self._tf[doc_id] = counts
        for term in set(counts):
            self._df[term] += 1

    def _idf(self, term: str) -> float:
        n = max(len(self._docs), 1)
        return math.log((n + 1) / (self._df.get(term, 0) + 1)) + 1.0

    def _vector(self, counts: Counter) -> Dict[str, float]:
        total = max(sum(counts.values()), 1)
        return {t: (c / total) * self._idf(t) for t, c in counts.items()}

    @staticmethod
    def _cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
        dot = sum(v * b.get(t, 0.0) for t, v in a.items())
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    def search(self, query: str, top_k: int = 3) -> List[Tuple[str, float, str]]:
        if not self._docs:
            return []
        qv = self._vector(Counter(_tokens(query)))
        scored = []
        for doc_id, counts in self._tf.items():
            score = self._cosine(qv, self._vector(counts))
            if score > 0:
                text = self._docs[doc_id]
                scored.append((doc_id, round(score, 4), text[:280]))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


BRAND_SEED = {
    "brand/voice-v1": (
        "Brand voice: clear, direct, helpful. Explain AI in simple Arabic first, "
        "then English terms. No hype, no exaggerated claims. Show real numbers, "
        "real screenshots, and one clear call to action per post."
    ),
    "brand/offers-4splus": (
        "Vo Technology offers 4S PLUS automotive ERP: Sales, Spare Parts, Service, "
        "and Survey. The Service module runs JobCards from work in progress to "
        "ready for invoicing, tracking actual versus sold hours."
    ),
}

PERSONAL_SEED = {
    "personal/weekly-goals": (
        "Weekly goals: ship the Vo Technology marketing agent proof of concept, "
        "keep the daily job applications running, publish LinkedIn page posts "
        "daily, and protect morning deep work blocks."
    ),
    "personal/preferences": (
        "Preferences: approvals before any publish or send, Arabic replies, "
        "short direct summaries, security alerts first in the morning briefing."
    ),
}


DOMAIN4S_SEED = {
    "domain4s/one-car-journey": (
        "One Car Journey: a car is sold in Sales with its chassis number, returns to "
        "Service where a JobCard opens with full history, parts are requested from the "
        "JobCard and issued from Spare Parts stock, the JobCard closes Ready for "
        "invoicing in Accounting, and CRM sends the satisfaction survey and the next "
        "predictive maintenance alert."
    ),
    "domain4s/service-jobcard": (
        "Service JobCard lifecycle: W.I.P work in progress, then Ready for invoicing. "
        "Operations track Actual hours versus Sold hours, sold rate and net. Menus: "
        "Service Packages, Periodic Maintenance Service, Appointments, QC CheckList, "
        "Follow Customer, Discount On Labour and Parts."
    ),
    "domain4s/lead-scoring": (
        "CRM AI lead scoring ranks dealer and workshop prospects by business fit, "
        "monthly volume, current system pain, and engagement signals like demo "
        "requests, then suggests the next action for each tier."
    ),
}


class KnowledgeBases:
    def __init__(self) -> None:
        self.brand = TfidfRetriever()
        self.personal = TfidfRetriever()
        self.domain4s = TfidfRetriever()
        for doc_id, text in BRAND_SEED.items():
            self.brand.add_document(doc_id, text)
        for doc_id, text in PERSONAL_SEED.items():
            self.personal.add_document(doc_id, text)
        for doc_id, text in DOMAIN4S_SEED.items():
            self.domain4s.add_document(doc_id, text)

    def get(self, collection: str) -> TfidfRetriever:
        return {"brand": self.brand, "personal": self.personal, "domain4s": self.domain4s}[collection]


KB = KnowledgeBases()
