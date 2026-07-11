-- Query ID: my_d2_easy_1
-- Source dialect: mysql
-- Target dataset: D2
-- Difficulty: easy
-- Description: Total OT paid across all employees
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT SUM(`Total_OT_Paid`) AS total_ot FROM `d2_table`