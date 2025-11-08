-- Query: full_outer_join
-- Dialect: postgresql
-- Complexity: 35
-- Difficulty: medium

SELECT * FROM table1 t1 FULL OUTER JOIN table2 t2 ON t1.id = t2.id;
