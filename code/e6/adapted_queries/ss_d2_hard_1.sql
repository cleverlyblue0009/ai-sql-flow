-- Query ID: ss_d2_hard_1
-- Source dialect: tsql
-- Target dataset: D2
-- Difficulty: hard
-- Description: Running total of gross pay ordered by agency (window frame)
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT [Agency_Name], [Last_Name], [Regular_Gross_Paid], SUM(CAST([Regular_Gross_Paid] AS BIGINT)) OVER (ORDER BY [Agency_Name], [Last_Name] ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total FROM [d2_table] WHERE [Pay_Basis] = 'per Annum' ORDER BY [Agency_Name], [Last_Name] OFFSET 0 ROWS FETCH NEXT 500 ROWS ONLY