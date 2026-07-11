-- Query ID: sf_d2_hard_1
-- Source dialect: snowflake
-- Target dataset: D2
-- Difficulty: hard
-- Description: CTE chain: identify high-OT agencies with low base pay
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

WITH agency_ot AS (  SELECT "Agency_Name",     AVG("Total_OT_Paid") AS avg_ot,     AVG("Base_Salary") AS avg_base   FROM "d2_table"   WHERE "Pay_Basis" = 'per Annum'   GROUP BY "Agency_Name" ), risk_agencies AS (  SELECT "Agency_Name", avg_ot, avg_base,     avg_ot / NULLIF(avg_base, 0) AS ot_base_ratio   FROM agency_ot   WHERE avg_ot > 10000 ) SELECT "Agency_Name",   ROUND(ot_base_ratio, 4) AS ot_base_ratio,   RANK() OVER (ORDER BY ot_base_ratio DESC) AS risk_rank FROM risk_agencies ORDER BY risk_rank LIMIT 10