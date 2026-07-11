-- Query ID: ss_d3_hard_1
-- Source dialect: tsql
-- Target dataset: D3
-- Difficulty: hard
-- Description: Running total bill with window frame
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT TOP 500 [ID], [EDUCATION], [BILL_AMT1], SUM(CAST([BILL_AMT1] AS BIGINT)) OVER (PARTITION BY [EDUCATION] ORDER BY [ID] ROWS UNBOUNDED PRECEDING) AS running_bill FROM [d3_table]