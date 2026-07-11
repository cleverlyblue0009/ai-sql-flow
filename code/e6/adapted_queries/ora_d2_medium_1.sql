-- Query ID: ora_d2_medium_1
-- Source dialect: oracle
-- Target dataset: D2
-- Difficulty: medium
-- Description: Agency average salary with RANK analytic function
-- Table placeholder: {table} → replaced with payroll_dirty/clean or credit_dirty/clean

SELECT "Agency_Name", AVG("Base_Salary") avg_sal, RANK() OVER (ORDER BY AVG("Base_Salary") DESC) AS sal_rank FROM "d2_table" GROUP BY "Agency_Name" ORDER BY sal_rank FETCH FIRST 10 ROWS ONLY