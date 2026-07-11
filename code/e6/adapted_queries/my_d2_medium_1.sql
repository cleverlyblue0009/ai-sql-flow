-- Query ID: my_d2_medium_1
-- Source dialect: mysql
-- Target dataset: D2
-- Difficulty: medium
-- Description: Title-level OT ratio with GROUP BY / HAVING
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT `Title_Description`, SUM(`Total_OT_Paid`) / NULLIF(SUM(`Regular_Gross_Paid`), 0) AS ot_ratio FROM `d2_table` GROUP BY `Title_Description` HAVING SUM(`Regular_Gross_Paid`) > 100000 ORDER BY ot_ratio DESC LIMIT 10