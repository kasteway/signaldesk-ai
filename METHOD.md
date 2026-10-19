# Measurement and interpretation

## Scope and completeness

- Source: official CFPB Consumer Complaint Database API.
- Filter: `product=Money transfer, virtual currency, or money service`; date received January 1–June 30, 2024.
- Pulled in three two-month partitions (2,592, 2,742, and 2,619 rows). Each API-returned total matched the number of records downloaded; all 7,953 IDs are unique.
- Committed fields: complaint ID, received date, product, sub-product, issue, sub-issue, state, submission channel, company response, and timely response flag. Missing values are retained as blank/unknown. No narratives, company names, or ZIP codes are committed.
- The API is live. Re-downloading later may change counts as records are corrected or added. `data/provenance.json` records retrieval time and a checksum.

## Screening rule

Records are grouped by Monday-start calendar week and issue. For each complete week, the expected issue count is the mean of the prior four complete weeks. A row enters the review queue when:

1. The observed count is at least 10.
2. The prior mean is at least 5.
3. Observed is at least 1.4 times the prior mean.
4. `(observed − expected) / sqrt(expected)` is at least 3.

This extract begins on Monday and ends on Sunday, so both edge weeks are complete. The first four weeks provide the initial baseline; scoring starts with the fifth week. This is a heuristic based on a Poisson-style variance assumption; it is not a calibrated probability or a causal result. It can be sensitive to seasonality, duplicate behavior, changing CFPB category definitions, and the fact that publication and complaint dates differ. An investigation should validate the source and compare with exposure denominators.

## Retrieval and MCP boundaries

`signaldesk.brief` indexes data-backed issue cards, flagged issue-week cards, and two method/scope cards. Its local term-weighted retrieval returns the strongest matching facts plus file citations. It does not send data to a hosted model or generate novel diagnoses. The MCP server exposes the same checked dataset to AI clients; any downstream language model must still distinguish facts from inference.

## What cannot be concluded

This demo cannot compare company risk, estimate consumer incidence or harm, prove fraud occurred, or attribute a count change to a particular process. A company operating many more transactions can have more complaints even with a lower per-transaction rate. CFPB says the database is not a statistical sample of consumer experience.
