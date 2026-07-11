-- Query ID: my_d3_easy_1
-- Source dialect: mysql
-- Target dataset: D3
-- Difficulty: easy
-- Description: Count zero-limit-balance accounts with outstanding bill
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT COUNT(*) AS zero_limit_with_bill FROM `d3_table` WHERE `LIMIT_BAL` = 0 AND `BILL_AMT1` > 0