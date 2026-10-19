# SignalDesk AI: study and interview guide

This is a compact guide to the **why, how, and limits** of the project. Each section points to the working code so you can refresh your memory before an interview.

## 1. The story to tell

> “I built a public-data prototype for financial-services operations. It ingests CFPB money-transfer complaints, validates the data, detects unusual weekly issue counts, and presents the results in a dashboard. A retrieval layer and MCP tools let an AI assistant answer questions with explicit source citations. I chose a transparent screen rather than pretending public complaints reveal root cause.”

**Why employers care:** It connects data engineering, measurement, AI interfaces, operational decisions, and responsible interpretation. It is intentionally different from a generic chatbot or a notebook-only model.

## 2. End-to-end flow

```text
CFPB public API → complete filtered extract → validation → weekly aggregates
                                             ↘ screening signals → dashboard
                                             ↘ evidence cards → retrieval → MCP tools
```

- **Data acquisition:** Three bounded CFPB API calls. Each returned record count must equal the API total. See [`data/provenance.json`](../data/provenance.json).
- **Validation:** Duplicate IDs, allowed date range, and expected product. See [`signaldesk/core.py`](../signaldesk/core.py).
- **Measurement:** Monday-start weekly totals and issue mix; the January–June 2024 extract consists of complete Monday–Sunday weeks, with the first four used as baseline.
- **Statistical screening:** Four-week mean plus absolute and relative thresholds. See [`METHOD.md`](../METHOD.md).
- **Evidence retrieval:** Local term weighting over computed cards; returns cited facts. See [`signaldesk/brief.py`](../signaldesk/brief.py).
- **Tool use:** An AI client can ask MCP for overview, signals, or cited evidence. See [`signaldesk/mcp_server.py`](../signaldesk/mcp_server.py).
- **User experience:** A static dashboard highlights scope, trend, issue mix, and review queue. See [`web/`](../web/).

## 3. Key concepts in plain English

**RAG (retrieval-augmented generation):** First find relevant evidence, then use it to answer. This project implements the retrieval and grounded-answer side locally. It does not claim an LLM was used to generate dashboard conclusions. To extend it, pass the retrieved cards to a model with a requirement to cite sources and refuse unsupported answers.

**MCP (Model Context Protocol):** A standard way for an AI client to discover and call tools. Here, the server offers three read-only tools over the same checked analysis. The client can choose a tool; the tool returns structured evidence rather than letting the model invent numbers.

**Alert screening versus prediction:** The project flags counts that exceed a recent baseline. It does not forecast the next week or predict individual complaints. This is a practical operational signal, but it should be validated against seasonality and exposure before business action.

**Data provenance:** The source URL, filters, retrieval time, partition counts, and SHA-256 checksum make the extract auditable. If the live CFPB database changes, the committed snapshot still supports reproducibility.

## 4. Walk through one real example

The largest issue is **Fraud or scam**: 2,929 of 7,953 in-scope complaints (36.8%). That tells an analyst the issue dominates this filtered complaint *mix*. It does **not** mean 36.8% of money-transfer customers experienced fraud. The dashboard also shows issue-week flags only when they pass the documented four-week screen. An analyst's next steps would be to check category consistency, volume denominators, channel shifts, and internal process data.

Try: `python3 -m signaldesk.brief "What happened with fraud or scam?"`.

## 5. How to demo it in three minutes

1. Open the dashboard. State the business question and the six-month scope.
2. Point to the weekly volume and issue mix; explain the difference between counts and rates.
3. Open the signal cards. Explain the four-week baseline and why a flag begins an investigation.
4. Run the question above and show its file citation.
5. Mention that the same facts are available as read-only MCP tools.
6. Close with the proposed production extension: add internal transaction denominators and an analyst review loop.

## 6. Likely interview questions

**“Where is the AI?”** The AI-ready parts are retrieval-grounded answers and MCP tool access. The dashboard’s screening is statistical analytics. I label those components precisely rather than calling every calculation AI.

**“Why no predictive model?”** Public complaints lack a reliable exposure denominator and operational outcome labels. A predictive model could look sophisticated but produce a misleading business claim. The transparent alert screen is the right prototype; validated internal outcomes would enable supervised modeling later.

**“How would you evaluate the assistant?”** Make a test set of factual, ambiguous, and unanswerable questions. Check citation accuracy, numeric agreement with the dashboard, refusal on unsupported claims, and latency. Add human review for high-stakes interpretations.

**“How would you make it production ready?”** Scheduled ingestion, immutable snapshots, schema checks, data access controls, monitoring, an exposure denominator, alert precision review, and a documented escalation owner.

## References

- [CFPB Consumer Complaint Database and interpretation guidance](https://www.consumerfinance.gov/data-research/consumer-complaints/)
- [CFPB API documentation](https://cfpb.github.io/api/ccdb/api.html)
- [CFPB database field reference](https://cfpb.github.io/api/ccdb/fields.html)
- [MCP specification](https://modelcontextprotocol.io/specification/2025-03-26)
