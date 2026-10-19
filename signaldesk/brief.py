"""Grounded, local retrieval over data-backed signal cards and method notes."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from .core import ROOT, build

STOP = {"the", "and", "for", "with", "what", "were", "that", "this", "from", "about", "did", "are", "our", "you", "how", "can", "why", "was"}


def tokens(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in STOP]


def cards(data: dict) -> list[dict]:
    result = [
        {"id": "method", "title": "Signal method", "text": data["method"] + " Complaint volume is not a measure of consumer harm or company risk without appropriate denominators.", "source": "METHOD.md"},
        {"id": "scope", "title": "Data scope", "text": f"{data['total']:,} public CFPB money-transfer complaints received {data['period']}. Fields are complaint categories, dates, state, channel, and response metadata. No narratives or company ranking are included.", "source": "data/provenance.json"},
    ]
    for item in data["issues"]:
        result.append({"id": "issue:" + item["name"], "title": item["name"], "text": f"{item['name']} appears in {item['count']:,} complaints ({item['count']/data['total']:.1%} of this filtered dataset). This is a complaint share, not a customer incidence rate.", "source": "web/dashboard.json"})
    for item in data["signals"]:
        result.append({"id": "signal:" + item["week"] + ":" + item["issue"], "title": item["issue"] + " · " + item["week"], "text": f"Week of {item['week']}: {item['issue']} had {item['observed']} complaints versus a four-week mean of {item['baseline']} ({item['change_pct']:+d}%, screening score {item['score']}). Investigate category mix and data quality before drawing conclusions.", "source": "web/dashboard.json"})
    return result


def retrieve(question: str, documents: list[dict], limit: int = 3) -> list[dict]:
    query = set(tokens(question))
    if not query:
        return []
    corpus = [Counter(tokens(d["title"] + " " + d["text"])) for d in documents]
    df = Counter(term for doc in corpus for term in doc)
    n = len(corpus)
    scored = []
    for document, terms in zip(documents, corpus):
        score = sum((1 + math.log(terms[t])) * math.log(1 + n / (1 + df[t])) for t in query if terms[t])
        if score:
            scored.append((score, document))
    return [d for _, d in sorted(scored, key=lambda x: -x[0])[:limit]]


def answer(question: str) -> dict:
    path = ROOT / "web" / "dashboard.json"
    data = json.loads(path.read_text()) if path.exists() else build()
    evidence = retrieve(question, cards(data))
    if not evidence:
        return {"answer": "I could not find a matching fact in the project evidence. Try an issue name or ask about the alert method.", "citations": []}
    return {"answer": " ".join(d["text"] for d in evidence), "citations": [d["source"] for d in evidence]}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ask a grounded question about SignalDesk")
    parser.add_argument("question")
    args = parser.parse_args()
    print(json.dumps(answer(args.question), indent=2))
