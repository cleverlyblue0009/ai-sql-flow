-- Query ID: my_d2_easy_2
-- Source dialect: mysql
-- Target dataset: D2
-- Difficulty: easy
-- Description: Count per-annum employees with very low gross pay
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT COUNT(*) AS suspect_count FROM `d2_table` WHERE `Pay_Basis` = 'per Annum' AND `Base_Salary` > 10000 AND `Regular_Gross_Paid` < `Base_Salary` * 0.05