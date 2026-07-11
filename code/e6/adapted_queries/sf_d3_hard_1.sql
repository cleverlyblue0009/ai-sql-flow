-- Query ID: sf_d3_hard_1
-- Source dialect: snowflake
-- Target dataset: D3
-- Difficulty: hard
-- Description: Multi-CTE: education × payment behaviour cross-tab
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

WITH edu_pay AS (  SELECT "EDUCATION", "PAY_0",     SUM("BILL_AMT1") AS total_bill,     SUM("PAY_AMT1") AS total_paid   FROM "d3_table"   GROUP BY "EDUCATION", "PAY_0" ), coverage AS (  SELECT "EDUCATION", "PAY_0", total_bill, total_paid,     total_paid / NULLIF(total_bill, 0) AS pay_coverage   FROM edu_pay ) SELECT "EDUCATION",   ROUND(AVG(pay_coverage), 4) AS avg_coverage FROM coverage GROUP BY "EDUCATION" ORDER BY "EDUCATION"