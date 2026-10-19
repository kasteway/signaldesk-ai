from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "cfpb_money_transfer_2024h1.csv"
OUT = ROOT / "web" / "dashboard.json"


def load_rows(path: Path = SOURCE) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    ids = [row["complaint_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate complaint IDs")
    for row in rows:
        day = date.fromisoformat(row["date_received"][:10])
        if not (date(2024, 1, 1) <= day <= date(2024, 6, 30)):
            raise ValueError("Date outside declared analysis window")
        if row["product"] != "Money transfer, virtual currency, or money service":
            raise ValueError("Unexpected product")
    return rows


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def analyze(rows: list[dict]) -> dict:
    by_week = Counter()
    issue_week = Counter()
    issue_total = Counter()
    product_total = Counter()
    channel_total = Counter()
    state_total = Counter()
    timely_total = Counter()
    for row in rows:
        week = week_start(date.fromisoformat(row["date_received"][:10])).isoformat()
        issue = row["issue"] or "Unspecified"
        by_week[week] += 1
        issue_week[(issue, week)] += 1
        issue_total[issue] += 1
        product_total[row["sub_product"] or "Unspecified"] += 1
        channel_total[row["submitted_via"] or "Unspecified"] += 1
        state_total[row["state"] or "Unknown"] += 1
        timely_total[row["timely"] or "Unknown"] += 1

    weeks = sorted(by_week)
    # The first and last weeks are partial calendar weeks; show them but do not alert on them.
    complete_weeks = [w for w in weeks if w >= "2024-01-08" and w <= "2024-06-17"]
    signals = []
    for issue, total in issue_total.items():
        if total < 100:
            continue
        for idx in range(4, len(complete_weeks)):
            target = complete_weeks[idx]
            history = [issue_week[(issue, w)] for w in complete_weeks[idx - 4:idx]]
            observed = issue_week[(issue, target)]
            expected = sum(history) / 4
            # Conservative Poisson-style screening score, not a calibrated probability.
            score = (observed - expected) / math.sqrt(max(expected, 1))
            if observed >= 10 and expected >= 5 and score >= 3 and observed >= 1.4 * expected:
                signals.append({"issue": issue, "week": target, "observed": observed,
                                "baseline": round(expected, 1), "score": round(score, 2),
                                "change_pct": round(100 * (observed / expected - 1))})
    signals.sort(key=lambda s: (-s["score"], s["week"]))

    def rank(counter: Counter, n: int) -> list[dict]:
        return [{"name": key, "count": value} for key, value in counter.most_common(n)]

    return {
        "title": "SignalDesk AI | Money transfer complaint intelligence",
        "source": "CFPB Consumer Complaint Database",
        "period": "2024-01-01 to 2024-06-30",
        "total": len(rows),
        "weeks": [{"week": w, "count": by_week[w]} for w in weeks],
        "issues": rank(issue_total, 12),
        "sub_products": rank(product_total, 7),
        "channels": rank(channel_total, 4),
        "states": rank(state_total, 12),
        "timeliness": rank(timely_total, 3),
        "signals": signals[:12],
        "method": "Four prior complete weeks; flag when count >=10, baseline >=5, score >=3 and observed >=1.4x baseline. Screening only.",
    }


def build() -> dict:
    result = analyze(load_rows())
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (OUT.parent / "data.js").write_text("window.SIGNALDESK_DATA = " + json.dumps(result, separators=(",", ":")) + ";\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = build()
    print(f"Built dashboard for {result['total']:,} records and {len(result['signals'])} signals")
