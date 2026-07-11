-- Query ID: pg_d2_hard_1
-- Source dialect: postgres
-- Target dataset: D2
-- Difficulty: hard
-- Description: CTE: near-duplicate names within same agency
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

WITH named AS (  SELECT "Agency_Name", "Last_Name",   COUNT(*) OVER (PARTITION BY "Agency_Name", "Last_Name") AS name_count   FROM d2_table) SELECT "Agency_Name", "Last_Name", MAX(name_count) AS dups FROM named WHERE name_count > 1 GROUP BY "Agency_Name", "Last_Name" ORDER BY dups DESC LIMIT 20