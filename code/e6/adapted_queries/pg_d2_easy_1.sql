-- Query ID: pg_d2_easy_1
-- Source dialect: postgres
-- Target dataset: D2
-- Difficulty: easy
-- Description: Average base salary across all employees
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT ROUND(AVG("Base_Salary"::numeric), 2) AS avg_salary FROM d2_table