-- Query ID: my_d3_hard_1
-- Source dialect: mysql
-- Target dataset: D3
-- Difficulty: hard
-- Description: CTE: accounts with bill exceeding limit
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

WITH risky AS ( SELECT `ID`, `LIMIT_BAL`, `BILL_AMT1`, `EDUCATION` FROM `d3_table` WHERE `BILL_AMT1` > `LIMIT_BAL` AND `LIMIT_BAL` > 0 ) SELECT `EDUCATION`, COUNT(*) AS n_risky, AVG(`BILL_AMT1`) AS avg_bill FROM risky GROUP BY `EDUCATION` ORDER BY n_risky DESC