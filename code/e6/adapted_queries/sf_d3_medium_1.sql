-- Query ID: sf_d3_medium_1
-- Source dialect: snowflake
-- Target dataset: D3
-- Difficulty: medium
-- Description: LAG window: month-over-month bill change
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT "ID", "EDUCATION", "BILL_AMT1", "BILL_AMT2", "BILL_AMT1" - "BILL_AMT2" AS bill_delta FROM "d3_table" WHERE ABS("BILL_AMT1" - "BILL_AMT2") > 50000 LIMIT 500