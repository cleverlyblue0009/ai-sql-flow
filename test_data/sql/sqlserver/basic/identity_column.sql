-- Query: identity_column
-- Dialect: sqlserver
-- Complexity: 35
-- Difficulty: easy

CREATE TABLE customers (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(255) UNIQUE,
    created_at DATETIME2 DEFAULT GETDATE()
);
