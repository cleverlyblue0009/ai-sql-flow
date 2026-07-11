-- Query ID: ss_d2_easy_1
-- Source dialect: tsql
-- Target dataset: D2
-- Difficulty: easy
-- Description: Max salary among per-annum employees
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT MAX([Base_Salary]) AS max_salary FROM [d2_table] WHERE [Pay_Basis] = 'per Annum'