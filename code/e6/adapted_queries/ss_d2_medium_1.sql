-- Query ID: ss_d2_medium_1
-- Source dialect: tsql
-- Target dataset: D2
-- Difficulty: medium
-- Description: Agency payroll summary with ROW_NUMBER window function
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT [Agency_Name], SUM([Regular_Gross_Paid]) AS total_gross, ROW_NUMBER() OVER (ORDER BY SUM([Regular_Gross_Paid]) DESC) AS rank FROM [d2_table] GROUP BY [Agency_Name] ORDER BY total_gross DESC