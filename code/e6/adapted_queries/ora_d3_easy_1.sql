-- Query ID: ora_d3_easy_1
-- Source dialect: oracle
-- Target dataset: D3
-- Difficulty: easy
-- Description: Count records with negative bill amount
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT COUNT(*) AS neg_bill FROM "d3_table" WHERE "BILL_AMT1" < 0