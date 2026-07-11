-- Query ID: ss_d3_medium_1
-- Source dialect: tsql
-- Target dataset: D3
-- Difficulty: medium
-- Description: Credit utilisation by age group (CASE bucketing)
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT CASE WHEN [AGE] < 30 THEN 'Under30'      WHEN [AGE] < 50 THEN '30-49' ELSE '50+' END AS age_group, AVG(CAST([BILL_AMT1] AS DECIMAL(18,2)) / NULLIF([LIMIT_BAL], 0)) AS util_ratio FROM [d3_table] WHERE [LIMIT_BAL] > 0 GROUP BY CASE WHEN [AGE] < 30 THEN 'Under30'               WHEN [AGE] < 50 THEN '30-49' ELSE '50+' END