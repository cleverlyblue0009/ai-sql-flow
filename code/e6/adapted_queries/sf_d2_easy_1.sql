-- Query ID: sf_d2_easy_1
-- Source dialect: snowflake
-- Target dataset: D2
-- Difficulty: easy
-- Description: Payroll count by work borough
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT "Work_Location_Borough", COUNT(*) AS headcount FROM "d2_table" GROUP BY "Work_Location_Borough" ORDER BY headcount DESC