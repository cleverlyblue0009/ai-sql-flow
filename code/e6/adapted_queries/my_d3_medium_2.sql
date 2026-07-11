-- Query ID: my_d3_medium_2
-- Source dialect: mysql
-- Target dataset: D3
-- Difficulty: medium
-- Description: Sex-based bill amount comparison
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT `SEX`, ROUND(AVG(`BILL_AMT1`), 2) AS avg_bill, ROUND(AVG(`LIMIT_BAL`), 2) AS avg_limit FROM `d3_table` GROUP BY `SEX`