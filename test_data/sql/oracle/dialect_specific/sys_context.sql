-- Query: sys_context
-- Dialect: oracle
-- Complexity: 30
-- Difficulty: hard
-- Dialect Features: SYS_CONTEXT

SELECT SYS_CONTEXT('USERENV', 'SESSION_USER') as current_user FROM DUAL;
