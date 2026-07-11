-- Query ID: ora_d3_hard_1
-- Source dialect: oracle
-- Target dataset: D3
-- Difficulty: hard
-- Description: Percentile-based credit risk segmentation
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT NTILE(4) OVER (ORDER BY "LIMIT_BAL") AS limit_quartile, COUNT(*) AS n, AVG("BILL_AMT1") AS avg_bill, SUM("default_payment_next_month") AS defaults FROM "d3_table" GROUP BY NTILE(4) OVER (ORDER BY "LIMIT_BAL") ORDER BY limit_quartile