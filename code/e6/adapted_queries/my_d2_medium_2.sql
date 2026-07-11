-- Query ID: my_d2_medium_2
-- Source dialect: mysql
-- Target dataset: D2
-- Difficulty: medium
-- Description: Pay basis distribution count
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT `Pay_Basis`, COUNT(*) AS n, ROUND(AVG(`Base_Salary`), 2) AS avg_base FROM `d2_table` GROUP BY `Pay_Basis` ORDER BY n DESC