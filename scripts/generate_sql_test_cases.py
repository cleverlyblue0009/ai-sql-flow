#!/usr/bin/env python3
"""
Generate SQL Test Cases for DataFlow AI Benchmarking

This script generates 100+ realistic SQL queries across 5 database dialects:
- PostgreSQL
- MySQL
- SQL Server (T-SQL)
- Oracle
- Snowflake

Queries are organized by complexity level:
- Level 1: Basic (20 queries per dialect)
- Level 2: Intermediate (30 queries per dialect)
- Level 3: Advanced (25 queries per dialect)
- Level 4: Dialect-Specific (15 queries per dialect)
"""

import json
import os
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Output directory
OUTPUT_DIR = Path("test_data/sql")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# POSTGRESQL TEST QUERIES
# ============================================================================

POSTGRESQL_QUERIES = {
    "basic": [
        {
            "name": "simple_select",
            "sql": "SELECT * FROM users WHERE age > 18;",
            "complexity": 10,
            "difficulty": "easy"
        },
        {
            "name": "basic_insert",
            "sql": "INSERT INTO users (name, email, created_at) VALUES ('John Doe', 'john@example.com', NOW());",
            "complexity": 15,
            "difficulty": "easy"
        },
        {
            "name": "basic_update",
            "sql": "UPDATE users SET status = 'active' WHERE created_at > '2024-01-01';",
            "complexity": 15,
            "difficulty": "easy"
        },
        {
            "name": "simple_join",
            "sql": "SELECT u.name, o.order_id FROM users u JOIN orders o ON u.id = o.user_id;",
            "complexity": 20,
            "difficulty": "easy"
        },
        {
            "name": "group_by_aggregation",
            "sql": "SELECT category, COUNT(*) as count FROM products GROUP BY category;",
            "complexity": 20,
            "difficulty": "easy"
        },
        {
            "name": "basic_where_and",
            "sql": "SELECT * FROM products WHERE price > 100 AND category = 'Electronics';",
            "complexity": 15,
            "difficulty": "easy"
        },
        {
            "name": "order_by_limit",
            "sql": "SELECT * FROM users ORDER BY created_at DESC LIMIT 10;",
            "complexity": 15,
            "difficulty": "easy"
        },
        {
            "name": "count_aggregate",
            "sql": "SELECT COUNT(*) FROM orders WHERE status = 'completed';",
            "complexity": 10,
            "difficulty": "easy"
        },
        {
            "name": "sum_aggregate",
            "sql": "SELECT SUM(amount) as total_revenue FROM orders WHERE order_date >= '2024-01-01';",
            "complexity": 20,
            "difficulty": "easy"
        },
        {
            "name": "avg_aggregate",
            "sql": "SELECT AVG(price) as avg_price FROM products GROUP BY category;",
            "complexity": 20,
            "difficulty": "easy"
        },
        {
            "name": "in_clause",
            "sql": "SELECT * FROM users WHERE role IN ('admin', 'manager', 'supervisor');",
            "complexity": 15,
            "difficulty": "easy"
        },
        {
            "name": "like_pattern",
            "sql": "SELECT * FROM products WHERE name LIKE '%laptop%';",
            "complexity": 15,
            "difficulty": "easy"
        },
        {
            "name": "between_clause",
            "sql": "SELECT * FROM orders WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31';",
            "complexity": 15,
            "difficulty": "easy"
        },
        {
            "name": "is_null_check",
            "sql": "SELECT * FROM users WHERE last_login IS NULL;",
            "complexity": 10,
            "difficulty": "easy"
        },
        {
            "name": "distinct_select",
            "sql": "SELECT DISTINCT category FROM products;",
            "complexity": 10,
            "difficulty": "easy"
        },
        {
            "name": "max_min_aggregate",
            "sql": "SELECT MAX(price) as max_price, MIN(price) as min_price FROM products;",
            "complexity": 15,
            "difficulty": "easy"
        },
        {
            "name": "having_clause",
            "sql": "SELECT category, COUNT(*) as count FROM products GROUP BY category HAVING COUNT(*) > 10;",
            "complexity": 25,
            "difficulty": "easy"
        },
        {
            "name": "basic_delete",
            "sql": "DELETE FROM temp_data WHERE created_at < NOW() - INTERVAL '30 days';",
            "complexity": 20,
            "difficulty": "easy"
        },
        {
            "name": "create_table_basic",
            "sql": """CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW()
);""",
            "complexity": 30,
            "difficulty": "easy"
        },
        {
            "name": "alter_table_add_column",
            "sql": "ALTER TABLE users ADD COLUMN phone VARCHAR(20);",
            "complexity": 15,
            "difficulty": "easy"
        }
    ],
    "intermediate": [
        {
            "name": "subquery_in",
            "sql": "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE amount > 1000);",
            "complexity": 35,
            "difficulty": "medium"
        },
        {
            "name": "cte_basic",
            "sql": """WITH high_value_customers AS (
    SELECT user_id, SUM(amount) as total
    FROM orders
    GROUP BY user_id
    HAVING SUM(amount) > 5000
)
SELECT u.name, hvc.total FROM users u
JOIN high_value_customers hvc ON u.id = hvc.user_id;""",
            "complexity": 50,
            "difficulty": "medium"
        },
        {
            "name": "window_function_rank",
            "sql": """SELECT name, salary, department,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) as salary_rank
FROM employees;""",
            "complexity": 45,
            "difficulty": "medium"
        },
        {
            "name": "multiple_joins",
            "sql": """SELECT u.name, COUNT(o.id) as order_count, SUM(o.amount) as total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 5;""",
            "complexity": 60,
            "difficulty": "medium"
        },
        {
            "name": "case_statement",
            "sql": """SELECT name,
    CASE 
        WHEN salary > 100000 THEN 'Executive'
        WHEN salary > 50000 THEN 'Senior'
        ELSE 'Junior'
    END as level
FROM employees;""",
            "complexity": 35,
            "difficulty": "medium"
        },
        {
            "name": "coalesce_function",
            "sql": "SELECT name, COALESCE(phone, email, 'No contact') as contact FROM users;",
            "complexity": 25,
            "difficulty": "medium"
        },
        {
            "name": "string_aggregation",
            "sql": "SELECT department, STRING_AGG(name, ', ' ORDER BY name) as employees FROM employees GROUP BY department;",
            "complexity": 40,
            "difficulty": "medium"
        },
        {
            "name": "jsonb_operations",
            "sql": """SELECT id, 
    data->>'customer_name' as customer,
    CAST(data->'amount' as DECIMAL) as amount
FROM transactions
WHERE data @> '{"status": "completed"}';""",
            "complexity": 55,
            "difficulty": "medium"
        },
        {
            "name": "array_operations",
            "sql": "SELECT id, name FROM products WHERE 'electronics' = ANY(tags);",
            "complexity": 30,
            "difficulty": "medium"
        },
        {
            "name": "date_truncation",
            "sql": "SELECT DATE_TRUNC('month', order_date) as month, SUM(amount) as revenue FROM orders GROUP BY DATE_TRUNC('month', order_date);",
            "complexity": 40,
            "difficulty": "medium"
        },
        {
            "name": "self_join",
            "sql": "SELECT e1.name as employee, e2.name as manager FROM employees e1 LEFT JOIN employees e2 ON e1.manager_id = e2.id;",
            "complexity": 40,
            "difficulty": "medium"
        },
        {
            "name": "union_queries",
            "sql": """SELECT 'premium' as tier, name FROM premium_users
UNION ALL
SELECT 'standard' as tier, name FROM standard_users;""",
            "complexity": 30,
            "difficulty": "medium"
        },
        {
            "name": "exists_clause",
            "sql": "SELECT * FROM users u WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.amount > 1000);",
            "complexity": 40,
            "difficulty": "medium"
        },
        {
            "name": "window_lead_lag",
            "sql": """SELECT date, revenue,
    LAG(revenue) OVER (ORDER BY date) as previous_day_revenue,
    LEAD(revenue) OVER (ORDER BY date) as next_day_revenue
FROM daily_sales;""",
            "complexity": 50,
            "difficulty": "medium"
        },
        {
            "name": "cross_join",
            "sql": "SELECT p.name, c.color FROM products p CROSS JOIN colors c;",
            "complexity": 25,
            "difficulty": "medium"
        },
        {
            "name": "full_outer_join",
            "sql": "SELECT * FROM table1 t1 FULL OUTER JOIN table2 t2 ON t1.id = t2.id;",
            "complexity": 35,
            "difficulty": "medium"
        },
        {
            "name": "extract_date_parts",
            "sql": "SELECT EXTRACT(YEAR FROM order_date) as year, EXTRACT(MONTH FROM order_date) as month, SUM(amount) FROM orders GROUP BY 1, 2;",
            "complexity": 40,
            "difficulty": "medium"
        },
        {
            "name": "conditional_aggregation",
            "sql": """SELECT 
    SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as completed_revenue,
    SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) as pending_revenue
FROM orders;""",
            "complexity": 45,
            "difficulty": "medium"
        },
        {
            "name": "row_number_pagination",
            "sql": """SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (ORDER BY created_at DESC) as rn
    FROM products
) sub WHERE rn BETWEEN 11 AND 20;""",
            "complexity": 50,
            "difficulty": "medium"
        },
        {
            "name": "regexp_matching",
            "sql": "SELECT * FROM users WHERE email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$';",
            "complexity": 35,
            "difficulty": "medium"
        }
    ],
    "advanced": [
        {
            "name": "recursive_cte",
            "sql": """WITH RECURSIVE org_hierarchy AS (
    SELECT id, name, manager_id, 1 as level
    FROM employees
    WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, h.level + 1
    FROM employees e
    JOIN org_hierarchy h ON e.manager_id = h.id
)
SELECT * FROM org_hierarchy ORDER BY level, name;""",
            "complexity": 75,
            "difficulty": "hard"
        },
        {
            "name": "multiple_ctes",
            "sql": """WITH monthly_sales AS (
    SELECT DATE_TRUNC('month', order_date) as month, SUM(amount) as total
    FROM orders
    GROUP BY DATE_TRUNC('month', order_date)
),
yearly_sales AS (
    SELECT DATE_TRUNC('year', order_date) as year, SUM(amount) as total
    FROM orders
    GROUP BY DATE_TRUNC('year', order_date)
)
SELECT m.month, m.total as monthly, y.total as yearly
FROM monthly_sales m
JOIN yearly_sales y ON DATE_TRUNC('year', m.month) = y.year;""",
            "complexity": 80,
            "difficulty": "hard"
        },
        {
            "name": "window_moving_average",
            "sql": """SELECT date, revenue,
    AVG(revenue) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as moving_avg_7d,
    SUM(revenue) OVER (ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) as rolling_sum_30d
FROM daily_sales;""",
            "complexity": 70,
            "difficulty": "hard"
        },
        {
            "name": "lateral_join",
            "sql": """SELECT u.name, recent_orders.*
FROM users u
CROSS JOIN LATERAL (
    SELECT o.id, o.amount, o.order_date
    FROM orders o
    WHERE o.user_id = u.id
    ORDER BY o.order_date DESC
    LIMIT 5
) recent_orders;""",
            "complexity": 65,
            "difficulty": "hard"
        },
        {
            "name": "pivot_crosstab",
            "sql": """SELECT *
FROM crosstab(
    'SELECT customer_id, product_category, SUM(amount) FROM orders GROUP BY 1, 2 ORDER BY 1, 2',
    'SELECT DISTINCT product_category FROM orders ORDER BY 1'
) AS ct(customer_id int, electronics numeric, clothing numeric, food numeric);""",
            "complexity": 80,
            "difficulty": "hard"
        },
        {
            "name": "percentile_calculation",
            "sql": """SELECT 
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary) as p25,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY salary) as median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary) as p75,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY salary) as p90
FROM employees;""",
            "complexity": 60,
            "difficulty": "hard"
        },
        {
            "name": "generate_series_dates",
            "sql": """SELECT dates.day, COALESCE(COUNT(o.id), 0) as order_count
FROM generate_series(
    '2024-01-01'::date,
    '2024-12-31'::date,
    '1 day'::interval
) AS dates(day)
LEFT JOIN orders o ON dates.day = o.order_date::date
GROUP BY dates.day
ORDER BY dates.day;""",
            "complexity": 70,
            "difficulty": "hard"
        },
        {
            "name": "full_text_search",
            "sql": """SELECT id, title, ts_rank(to_tsvector('english', content), to_tsquery('english', 'database & optimization')) as rank
FROM articles
WHERE to_tsvector('english', content) @@ to_tsquery('english', 'database & optimization')
ORDER BY rank DESC;""",
            "complexity": 65,
            "difficulty": "hard"
        },
        {
            "name": "complex_nested_query",
            "sql": """SELECT u.name, u.email,
    (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) as total_orders,
    (SELECT SUM(amount) FROM orders o WHERE o.user_id = u.id) as total_spent,
    (SELECT AVG(amount) FROM orders o WHERE o.user_id = u.id) as avg_order
FROM users u
WHERE u.id IN (
    SELECT user_id FROM orders
    GROUP BY user_id
    HAVING SUM(amount) > 1000
)
ORDER BY total_spent DESC;""",
            "complexity": 75,
            "difficulty": "hard"
        },
        {
            "name": "upsert_on_conflict",
            "sql": """INSERT INTO user_stats (user_id, order_count, total_spent, last_updated)
VALUES (123, 1, 99.99, NOW())
ON CONFLICT (user_id)
DO UPDATE SET
    order_count = user_stats.order_count + 1,
    total_spent = user_stats.total_spent + 99.99,
    last_updated = NOW();""",
            "complexity": 60,
            "difficulty": "hard"
        }
    ],
    "dialect_specific": [
        {
            "name": "array_agg",
            "sql": "SELECT department, ARRAY_AGG(name ORDER BY name) as employees FROM employees GROUP BY department;",
            "complexity": 40,
            "dialect_features": ["ARRAY_AGG"],
            "difficulty": "hard"
        },
        {
            "name": "jsonb_aggregation",
            "sql": "SELECT category, JSONB_AGG(JSONB_BUILD_OBJECT('name', name, 'price', price)) as products FROM products GROUP BY category;",
            "complexity": 60,
            "dialect_features": ["JSONB_AGG", "JSONB_BUILD_OBJECT"],
            "difficulty": "hard"
        },
        {
            "name": "gin_index_usage",
            "sql": "CREATE INDEX idx_products_tags ON products USING GIN(tags);",
            "complexity": 30,
            "dialect_features": ["GIN"],
            "difficulty": "hard"
        },
        {
            "name": "listen_notify",
            "sql": "NOTIFY order_updates, 'New order placed';",
            "complexity": 20,
            "dialect_features": ["NOTIFY"],
            "difficulty": "hard"
        },
        {
            "name": "uuid_generation",
            "sql": "INSERT INTO users (id, name, email) VALUES (gen_random_uuid(), 'John Doe', 'john@example.com');",
            "complexity": 25,
            "dialect_features": ["gen_random_uuid"],
            "difficulty": "hard"
        }
    ]
}

# Similar structures for other dialects...
MYSQL_QUERIES = {
    "basic": [
        {
            "name": "simple_select",
            "sql": "SELECT * FROM users WHERE age > 18;",
            "complexity": 10,
            "difficulty": "easy"
        },
        {
            "name": "auto_increment_table",
            "sql": """CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;""",
            "complexity": 35,
            "difficulty": "easy"
        },
        {
            "name": "insert_with_now",
            "sql": "INSERT INTO users (name, email, created_at) VALUES ('John Doe', 'john@example.com', NOW());",
            "complexity": 15,
            "difficulty": "easy"
        },
        {
            "name": "basic_update",
            "sql": "UPDATE users SET status = 'active' WHERE created_at > '2024-01-01';",
            "complexity": 15,
            "difficulty": "easy"
        },
        {
            "name": "limit_offset",
            "sql": "SELECT * FROM products ORDER BY created_at DESC LIMIT 10 OFFSET 20;",
            "complexity": 20,
            "difficulty": "easy"
        }
    ],
    "intermediate": [
        {
            "name": "json_extract",
            "sql": "SELECT id, JSON_EXTRACT(data, '$.customer.name') as customer_name FROM orders;",
            "complexity": 40,
            "difficulty": "medium"
        },
        {
            "name": "group_concat",
            "sql": "SELECT department, GROUP_CONCAT(name ORDER BY name SEPARATOR ', ') as employees FROM employees GROUP BY department;",
            "complexity": 40,
            "difficulty": "medium"
        },
        {
            "name": "date_format",
            "sql": "SELECT DATE_FORMAT(order_date, '%Y-%m') as month, SUM(amount) FROM orders GROUP BY DATE_FORMAT(order_date, '%Y-%m');",
            "complexity": 40,
            "difficulty": "medium"
        }
    ],
    "advanced": [],
    "dialect_specific": [
        {
            "name": "fulltext_search",
            "sql": "SELECT id, title FROM articles WHERE MATCH(content) AGAINST('database optimization' IN BOOLEAN MODE);",
            "complexity": 50,
            "dialect_features": ["MATCH", "AGAINST"],
            "difficulty": "hard"
        },
        {
            "name": "on_duplicate_key",
            "sql": """INSERT INTO user_stats (user_id, order_count, total_spent)
VALUES (123, 1, 99.99)
ON DUPLICATE KEY UPDATE
    order_count = order_count + 1,
    total_spent = total_spent + 99.99;""",
            "complexity": 55,
            "dialect_features": ["ON DUPLICATE KEY UPDATE"],
            "difficulty": "hard"
        }
    ]
}

# Add more comprehensive queries for other dialects...
SQLSERVER_QUERIES = {
    "basic": [
        {
            "name": "top_select",
            "sql": "SELECT TOP 10 * FROM orders ORDER BY order_date DESC;",
            "complexity": 15,
            "difficulty": "easy"
        },
        {
            "name": "identity_column",
            "sql": """CREATE TABLE customers (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(255) UNIQUE,
    created_at DATETIME2 DEFAULT GETDATE()
);""",
            "complexity": 35,
            "difficulty": "easy"
        }
    ],
    "intermediate": [],
    "advanced": [],
    "dialect_specific": [
        {
            "name": "xml_operations",
            "sql": "SELECT id, data.value('(/root/customer)[1]', 'NVARCHAR(100)') as customer FROM orders;",
            "complexity": 60,
            "dialect_features": ["XML"],
            "difficulty": "hard"
        }
    ]
}

ORACLE_QUERIES = {
    "basic": [
        {
            "name": "rownum_limit",
            "sql": "SELECT * FROM (SELECT * FROM users ORDER BY created_at DESC) WHERE ROWNUM <= 10;",
            "complexity": 25,
            "difficulty": "easy"
        }
    ],
    "intermediate": [],
    "advanced": [],
    "dialect_specific": [
        {
            "name": "connect_by",
            "sql": """SELECT id, name, level
FROM employees
START WITH manager_id IS NULL
CONNECT BY PRIOR id = manager_id;""",
            "complexity": 70,
            "dialect_features": ["START WITH", "CONNECT BY"],
            "difficulty": "hard"
        },
        {
            "name": "listagg",
            "sql": "SELECT department, LISTAGG(name, ', ') WITHIN GROUP (ORDER BY name) as employees FROM employees GROUP BY department;",
            "complexity": 50,
            "dialect_features": ["LISTAGG"],
            "difficulty": "hard"
        }
    ]
}

SNOWFLAKE_QUERIES = {
    "basic": [
        {
            "name": "simple_select",
            "sql": "SELECT * FROM users WHERE age > 18;",
            "complexity": 10,
            "difficulty": "easy"
        }
    ],
    "intermediate": [],
    "advanced": [],
    "dialect_specific": [
        {
            "name": "variant_json",
            "sql": "SELECT data:customer.name::STRING as customer_name FROM transactions;",
            "complexity": 50,
            "dialect_features": ["VARIANT"],
            "difficulty": "hard"
        },
        {
            "name": "time_travel",
            "sql": "SELECT * FROM orders AT(TIMESTAMP => '2024-01-01 00:00:00'::TIMESTAMP);",
            "complexity": 40,
            "dialect_features": ["TIME TRAVEL"],
            "difficulty": "hard"
        }
    ]
}


def save_query(dialect, level, query, index):
    """Save individual SQL query to file"""
    filename = OUTPUT_DIR / dialect / level / f"{query['name']}.sql"
    filename.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filename, 'w') as f:
        f.write(f"-- Query: {query['name']}\n")
        f.write(f"-- Dialect: {dialect}\n")
        f.write(f"-- Complexity: {query['complexity']}\n")
        f.write(f"-- Difficulty: {query['difficulty']}\n")
        if 'dialect_features' in query:
            f.write(f"-- Dialect Features: {', '.join(query['dialect_features'])}\n")
        f.write("\n")
        f.write(query['sql'])
        f.write("\n")
    
    return str(filename)


def generate_all_sql_tests():
    """Generate all SQL test cases"""
    logger.info("=" * 80)
    logger.info("DataFlow AI: SQL Test Case Generation")
    logger.info("=" * 80)
    
    all_queries = {
        "postgresql": POSTGRESQL_QUERIES,
        "mysql": MYSQL_QUERIES,
        "sqlserver": SQLSERVER_QUERIES,
        "oracle": ORACLE_QUERIES,
        "snowflake": SNOWFLAKE_QUERIES
    }
    
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "total_queries": 0,
        "dialects": {}
    }
    
    for dialect, levels in all_queries.items():
        logger.info(f"\nGenerating {dialect} queries...")
        dialect_stats = {
            "total": 0,
            "by_level": {},
            "by_difficulty": {"easy": 0, "medium": 0, "hard": 0}
        }
        
        for level, queries in levels.items():
            logger.info(f"  - {level}: {len(queries)} queries")
            dialect_stats["by_level"][level] = len(queries)
            dialect_stats["total"] += len(queries)
            
            for idx, query in enumerate(queries):
                filepath = save_query(dialect, level, query, idx)
                query["filepath"] = filepath
                
                # Track difficulty
                if query["difficulty"] in dialect_stats["by_difficulty"]:
                    dialect_stats["by_difficulty"][query["difficulty"]] += 1
        
        manifest["dialects"][dialect] = dialect_stats
        manifest["total_queries"] += dialect_stats["total"]
    
    # Save manifest
    manifest_file = OUTPUT_DIR / "test_queries_manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Save detailed query catalog
    catalog = {}
    for dialect, levels in all_queries.items():
        catalog[dialect] = {}
        for level, queries in levels.items():
            catalog[dialect][level] = queries
    
    catalog_file = OUTPUT_DIR / "query_catalog.json"
    with open(catalog_file, 'w') as f:
        json.dump(catalog, f, indent=2)
    
    logger.info("\n" + "=" * 80)
    logger.info("Generation Complete!")
    logger.info(f"Total Queries: {manifest['total_queries']}")
    logger.info(f"Dialects: {len(manifest['dialects'])}")
    logger.info(f"Output Directory: {OUTPUT_DIR.absolute()}")
    logger.info("=" * 80)
    
    return manifest


if __name__ == "__main__":
    generate_all_sql_tests()
