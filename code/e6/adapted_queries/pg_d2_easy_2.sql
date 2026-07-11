-- Query ID: pg_d2_easy_2
-- Source dialect: postgres
-- Target dataset: D2
-- Difficulty: easy
-- Description: Count employees with OT pay but zero regular hours
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT COUNT(*) AS suspicious_ot FROM d2_table WHERE "Total_OT_Paid" > 0 AND "Regular_Hours" = 0