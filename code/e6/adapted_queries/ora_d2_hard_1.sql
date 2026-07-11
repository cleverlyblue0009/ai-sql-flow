-- Query ID: ora_d2_hard_1
-- Source dialect: oracle
-- Target dataset: D2
-- Difficulty: hard
-- Description: Recursive CTE: agencies with OT > 20% of gross pay
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

WITH agency_stats AS (SELECT "Agency_Name", SUM("Total_OT_Paid") AS total_ot, SUM("Regular_Gross_Paid") AS total_gross FROM "d2_table" GROUP BY "Agency_Name") SELECT "Agency_Name", ROUND(total_ot / NULLIF(total_gross, 0), 4) AS ot_pct FROM agency_stats WHERE total_ot / NULLIF(total_gross, 0) > 0.20 ORDER BY ot_pct DESC