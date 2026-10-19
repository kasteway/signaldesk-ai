-- SignalDesk reproducibility check, run against the CSV loaded into complaints.
-- One row per public CFPB complaint; no narrative or company fields.
SELECT issue, COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM complaints), 1) AS share_pct
FROM complaints
GROUP BY issue
ORDER BY complaints DESC;

SELECT substr(date_received, 1, 7) AS received_month,
       sub_product, COUNT(*) AS complaints
FROM complaints
GROUP BY received_month, sub_product
ORDER BY received_month, complaints DESC;
