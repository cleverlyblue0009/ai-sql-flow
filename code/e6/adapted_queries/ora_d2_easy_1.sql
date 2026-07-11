-- Query ID: ora_d2_easy_1
-- Source dialect: oracle
-- Target dataset: D2
-- Difficulty: easy
-- Description: Sum of regular gross paid for firefighters
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT SUM("Regular_Gross_Paid") AS firefighter_gross FROM "d2_table" WHERE UPPER("Title_Description") LIKE '%FIREFIGHTER%'