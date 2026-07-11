-- Query ID: sf_d2_medium_1
-- Source dialect: snowflake
-- Target dataset: D2
-- Difficulty: medium
-- Description: QUALIFY clause: top earner per agency
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT "Agency_Name", "Last_Name", "Base_Salary", RANK() OVER (PARTITION BY "Agency_Name" ORDER BY "Base_Salary" DESC) AS rnk FROM "d2_table" QUALIFY rnk = 1