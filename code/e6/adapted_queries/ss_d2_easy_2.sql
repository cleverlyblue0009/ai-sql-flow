-- Query ID: ss_d2_easy_2
-- Source dialect: tsql
-- Target dataset: D2
-- Difficulty: easy
-- Description: Count suspicious agency-title combinations
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT COUNT(*) AS title_violations FROM [d2_table] WHERE [Title_Description] LIKE '%TEACHER%' AND [Agency_Name] NOT LIKE '%EDUCATION%' AND [Agency_Name] NOT LIKE '%DEPT OF ED%'