-- Query ID: my_d2_hard_1
-- Source dialect: mysql
-- Target dataset: D2
-- Difficulty: hard
-- Description: Agency headcount and total pay with window SUM
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT `Agency_Name`, COUNT(*) AS n, SUM(`Regular_Gross_Paid`) AS agency_total, SUM(SUM(`Regular_Gross_Paid`)) OVER () AS grand_total, ROUND(SUM(`Regular_Gross_Paid`) / SUM(SUM(`Regular_Gross_Paid`)) OVER (), 4) AS share FROM `d2_table` GROUP BY `Agency_Name` ORDER BY agency_total DESC LIMIT 10