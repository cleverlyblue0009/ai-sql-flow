# OpenAI-Powered SQL Translation Setup Guide

## Overview

The SQL translation engine has been upgraded to use OpenAI's GPT-4 API for significantly improved translation accuracy. The system now intelligently translates SQL between different dialects (MySQL, PostgreSQL, SQL Server, Oracle, Snowflake) with better understanding of context, semantics, and dialect-specific features.

## Key Improvements

### Before (Rule-Based)
- ❌ Simple regex pattern matching
- ❌ Limited understanding of context
- ❌ Missed edge cases and complex queries
- ❌ No semantic understanding
- ❌ Fixed transformation rules

### After (AI-Powered with OpenAI)
- ✅ Deep understanding of SQL semantics
- ✅ Context-aware translations
- ✅ Handles complex queries and edge cases
- ✅ Learns from dialect-specific patterns
- ✅ Provides optimization suggestions
- ✅ Automatic fallback to rule-based translation if API is unavailable

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the `openai` package along with other dependencies.

### 2. Get OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Navigate to API Keys section
4. Click "Create new secret key"
5. Copy the key (it starts with `sk-`)

### 3. Configure Environment Variables

Add to your `.env` file:

```bash
# OpenAI API (Required for AI-powered SQL translation)
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Important**: 
- Keep your API key secure and never commit it to version control
- The `.env` file is already in `.gitignore`

### 4. Restart the Application

```bash
# Stop the current server (Ctrl+C)
# Restart with:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## How It Works

### Translation Flow

1. **User submits SQL for translation**
   - SQL is analyzed for structure and complexity
   - Tables, functions, and dialect-specific features are identified

2. **OpenAI API Translation** (Primary Method)
   - SQL is sent to GPT-4 with expert system prompts
   - Context about source/target dialects is provided
   - AI understands semantics and applies proper conversions
   - Returns translated SQL + optimization suggestions

3. **Rule-Based Fallback** (If API unavailable)
   - Uses regex-based pattern matching
   - Applies predefined transformation rules
   - Still functional but less accurate

### AI Translation Features

The OpenAI integration provides:

- **Semantic Understanding**: Understands query intent, not just syntax
- **Data Type Conversion**: Proper mapping between dialect-specific types
  - MySQL `AUTO_INCREMENT` → Snowflake `AUTOINCREMENT`
  - PostgreSQL `SERIAL` → Snowflake `AUTOINCREMENT`
  - SQL Server `IDENTITY` → Snowflake `AUTOINCREMENT`
  - And many more...

- **Function Translation**: Maps functions accurately
  - MySQL `NOW()` → Snowflake `CURRENT_TIMESTAMP()`
  - SQL Server `GETDATE()` → Snowflake `CURRENT_TIMESTAMP()`
  - PostgreSQL `AGE()` → Snowflake `DATEDIFF()`

- **Syntax Conversion**: Handles quoting and syntax differences
  - MySQL backticks `` ` `` → Snowflake double quotes `"`
  - SQL Server brackets `[]` → Snowflake double quotes `"`

- **Optimization Suggestions**: Provides dialect-specific recommendations
  - Clustering keys for Snowflake
  - Index suggestions
  - Performance improvements

## Example Translations

### MySQL to Snowflake

**Input (MySQL):**
```sql
CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `email` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `status` ENUM('active', 'inactive') DEFAULT 'active'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Output (Snowflake) - AI-Powered:**
```sql
CREATE TABLE "users" (
  "id" INT AUTOINCREMENT PRIMARY KEY,
  "email" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  "status" VARCHAR(10) DEFAULT 'active'
    CHECK ("status" IN ('active', 'inactive'))
);
```

**Optimization Suggestions:**
- Consider adding clustering keys on frequently queried columns
- Use VARIANT type for flexible schema columns if needed
- Enable result caching for frequently executed queries

### PostgreSQL to Snowflake

**Input (PostgreSQL):**
```sql
SELECT 
  u.username,
  COUNT(o.id) as order_count,
  COALESCE(SUM(o.total), 0) as total_spent,
  AGE(NOW(), u.created_at) as account_age
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
GROUP BY u.id, u.username, u.created_at
HAVING COUNT(o.id) > 5
ORDER BY total_spent DESC
LIMIT 100;
```

**Output (Snowflake) - AI-Powered:**
```sql
SELECT 
  u.username,
  COUNT(o.id) as order_count,
  COALESCE(SUM(o.total), 0) as total_spent,
  DATEDIFF('day', u.created_at, CURRENT_TIMESTAMP()) as account_age_days
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
GROUP BY u.id, u.username, u.created_at
HAVING COUNT(o.id) > 5
ORDER BY total_spent DESC
LIMIT 100;
```

## Cost Considerations

- **Model Used**: GPT-4o (optimized for quality and cost)
- **Average Cost**: ~$0.01-0.05 per translation
- **Optimization**: Low temperature (0.1) for consistent results
- **Fallback**: Free rule-based translation if API quota exceeded

## Monitoring

Check logs for translation method used:

```
INFO: Using OpenAI API for SQL translation
INFO: Successfully translated SQL using OpenAI API
```

Or if fallback is used:

```
INFO: Using rule-based translation (OpenAI API not available)
```

## Troubleshooting

### Issue: "OpenAI API key not configured"

**Solution**: Add `OPENAI_API_KEY` to your `.env` file

### Issue: API errors or rate limits

**Solution**: The system automatically falls back to rule-based translation. Check your OpenAI account quota.

### Issue: Translations not as expected

**Solution**: 
1. Ensure you're using the latest code
2. Check if API key is valid
3. Review logs for any errors
4. Try with optimization level "aggressive" for better results

## Testing

You can test the translation through:

1. **Web UI**: Upload SQL file and select source/target dialects
2. **API Endpoint**: 
   ```bash
   curl -X POST "http://localhost:8000/api/migrations/translate" \
     -H "Content-Type: application/json" \
     -d '{
       "source_sql": "SELECT NOW()",
       "source_dialect": "mysql",
       "target_dialect": "snowflake"
     }'
   ```

3. **Compare Results**: Try same SQL with and without API key to see the difference

## Support

For issues or questions:
- Check application logs
- Review OpenAI API status
- Ensure all environment variables are set correctly
