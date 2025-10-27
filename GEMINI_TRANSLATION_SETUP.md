# Google Gemini-Powered SQL Translation Setup Guide

## Overview

The SQL translation engine has been upgraded to use **Google Gemini 1.5 Pro API** for significantly improved translation accuracy. The system now intelligently translates SQL between different dialects (MySQL, PostgreSQL, SQL Server, Oracle, Snowflake) with better understanding of context, semantics, and dialect-specific features.

## Key Improvements

### Before (Rule-Based)
- ❌ Simple regex pattern matching
- ❌ Limited understanding of context
- ❌ Missed edge cases and complex queries
- ❌ No semantic understanding
- ❌ Fixed transformation rules

### After (AI-Powered with Gemini)
- ✅ Deep understanding of SQL semantics with Gemini 1.5 Pro
- ✅ Context-aware translations
- ✅ Handles complex queries and edge cases
- ✅ Learns from dialect-specific patterns
- ✅ Provides optimization suggestions
- ✅ Automatic fallback to rule-based translation if API is unavailable
- ✅ **FREE** generous quota from Google AI Studio

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the `google-generativeai` package along with other dependencies.

### 2. Get Google Gemini API Key (FREE)

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Select or create a Google Cloud project
5. Copy the API key

**Note:** Gemini API offers a generous free tier:
- 60 requests per minute
- 1500 requests per day
- Perfect for SQL translation workloads

### 3. Configure Environment Variables

Add to your `.env` file:

```bash
# Google Gemini API (Required for AI-powered SQL translation)
GEMINI_API_KEY=your-actual-gemini-api-key-here

# Or use the alternative env var name
# GOOGLE_API_KEY=your-actual-gemini-api-key-here
```

**Important**: 
- Keep your API key secure and never commit it to version control
- The `.env` file is already in `.gitignore`
- You can use either `GEMINI_API_KEY` or `GOOGLE_API_KEY` env var name

### 4. Restart the Application

```bash
# Stop the current server (Ctrl+C)
# Restart with:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see in the logs:
```
INFO: Google Gemini API initialized successfully for SQL translation
```

## How It Works

### Translation Flow

1. **User submits SQL for translation**
   - SQL is analyzed for structure and complexity
   - Tables, functions, and dialect-specific features are identified

2. **Gemini API Translation** (Primary Method)
   - SQL is sent to Gemini 1.5 Pro with expert system prompts
   - Context about source/target dialects is provided
   - AI understands semantics and applies proper conversions
   - Returns translated SQL + optimization suggestions

3. **Rule-Based Fallback** (If API unavailable)
   - Uses regex-based pattern matching
   - Applies predefined transformation rules
   - Still functional but less accurate

### AI Translation Features

The Gemini integration provides:

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
  - Oracle `SYSDATE` → Snowflake `CURRENT_TIMESTAMP()`

- **Syntax Conversion**: Handles quoting and syntax differences
  - MySQL backticks `` ` `` → Snowflake double quotes `"`
  - SQL Server brackets `[]` → Snowflake double quotes `"`
  - PostgreSQL dollar quotes `$$` → Standard quotes

- **Optimization Suggestions**: Provides dialect-specific recommendations
  - Clustering keys for Snowflake
  - Index suggestions
  - Partitioning recommendations
  - Performance improvements

## Example Translations

### MySQL to Snowflake

**Input (MySQL):**
```sql
CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `email` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `status` ENUM('active', 'inactive') DEFAULT 'active',
  `metadata` JSON
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Output (Snowflake) - AI-Powered:**
```sql
CREATE TABLE "users" (
  "id" INT AUTOINCREMENT PRIMARY KEY,
  "email" VARCHAR(255) NOT NULL,
  "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  "status" VARCHAR(10) DEFAULT 'active'
    CHECK ("status" IN ('active', 'inactive')),
  "metadata" VARIANT
);
```

**Optimization Suggestions:**
- Consider adding clustering keys on frequently queried columns like "email" or "created_at"
- Use VARIANT type for JSON data enables native JSON querying in Snowflake
- Enable result caching for frequently executed queries
- Consider adding indexes on filter columns

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
  AND u.created_at >= NOW() - INTERVAL '1 year'
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
  AND u.created_at >= DATEADD('year', -1, CURRENT_TIMESTAMP())
GROUP BY u.id, u.username, u.created_at
HAVING COUNT(o.id) > 5
ORDER BY total_spent DESC
LIMIT 100;
```

**Optimization Suggestions:**
- Add clustering key on u.created_at for time-based filtering
- Create index on u.status for WHERE clause optimization
- Consider result caching if this query runs frequently

### SQL Server to Snowflake

**Input (SQL Server):**
```sql
SELECT TOP 50
  [CustomerID],
  [OrderDate],
  DATEDIFF(day, [OrderDate], GETDATE()) as DaysSinceOrder,
  ISNULL([ShippingAddress], 'N/A') as ShippingAddress
FROM [dbo].[Orders] WITH (NOLOCK)
WHERE [Status] = 'Completed'
  AND [OrderDate] >= DATEADD(month, -6, GETDATE())
ORDER BY [OrderDate] DESC;
```

**Output (Snowflake) - AI-Powered:**
```sql
SELECT
  "CustomerID",
  "OrderDate",
  DATEDIFF('day', "OrderDate", CURRENT_TIMESTAMP()) as DaysSinceOrder,
  NVL("ShippingAddress", 'N/A') as ShippingAddress
FROM "dbo"."Orders"
WHERE "Status" = 'Completed'
  AND "OrderDate" >= DATEADD('month', -6, CURRENT_TIMESTAMP())
ORDER BY "OrderDate" DESC
LIMIT 50;
```

## Why Gemini Over Other Options?

### Advantages of Google Gemini

1. **Free Tier**: Generous free quota perfect for SQL translation
2. **Quality**: Gemini 1.5 Pro matches GPT-4 quality for technical tasks
3. **Speed**: Fast response times with low latency
4. **Context Window**: Large 1M token context window for complex schemas
5. **No Credit Card**: Start using immediately with just a Google account
6. **Cost-Effective**: Much cheaper than OpenAI when scaling

### Comparison

| Feature | Gemini 1.5 Pro | GPT-4 | Rule-Based |
|---------|---------------|-------|------------|
| Accuracy | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Cost | Free tier / Very cheap | Expensive | Free |
| Speed | Fast | Fast | Very Fast |
| Context Understanding | Excellent | Excellent | Poor |
| Setup | Easy | Requires payment | No setup |

## Cost & Rate Limits

### Free Tier (More than enough for most users)
- **15 requests per minute**
- **1,500 requests per day**
- **1 million requests per month**

For SQL translation, this means:
- ~1,500 SQL translations per day FREE
- Each translation completes in 1-3 seconds
- More than sufficient for typical development workflows

### Paid Tier (if you exceed free tier)
- **$0.35 per 1M input tokens**
- **$0.70 per 1M output tokens**
- Typical SQL translation: $0.001 - $0.01 per translation

## Monitoring

### Check Logs

Successful API usage:
```
INFO: Google Gemini API initialized successfully for SQL translation
INFO: Using Google Gemini API for SQL translation
INFO: Calling Google Gemini API for mysql to snowflake translation
INFO: Successfully translated SQL using Google Gemini API
```

Fallback to rule-based:
```
INFO: Gemini API key not configured. Using rule-based translation.
INFO: Using rule-based translation (Gemini API not available)
```

### Translation Metadata

Each translation response includes:
```json
{
  "translated_sql": "...",
  "confidence_score": 0.95,
  "semantic_similarity": 0.92,
  "translation_method": "gemini_api",
  "optimization_suggestions": [...]
}
```

## Troubleshooting

### Issue: "Gemini API key not configured"

**Solution**: 
1. Check your `.env` file has `GEMINI_API_KEY` or `GOOGLE_API_KEY`
2. Ensure the API key is valid (starts with proper prefix)
3. Restart the application after adding the key

### Issue: API errors or rate limits

**Solution**: 
- The system automatically falls back to rule-based translation
- Check your API quota at [Google AI Studio](https://aistudio.google.com)
- Consider spacing out bulk translation requests
- For large migrations, process in batches

### Issue: Translations not as expected

**Solution**: 
1. Ensure you're using the latest code
2. Check if API key is valid at Google AI Studio
3. Review logs for any errors
4. Try with optimization level "aggressive" for better results
5. Provide schema context for more accurate translations

### Issue: "Failed to initialize Gemini API"

**Common causes:**
- Invalid API key format
- Network connectivity issues
- Google AI Studio service temporarily unavailable

**Solution:**
- Verify API key at [Google AI Studio](https://aistudio.google.com/app/apikey)
- Check network/firewall settings
- System will automatically fall back to rule-based translation

## Testing the Integration

### 1. Via Web UI
1. Navigate to the SQL Migration page
2. Upload a SQL file or paste SQL code
3. Select source dialect (e.g., MySQL)
4. Select target dialect (e.g., Snowflake)
5. Click "Translate"
6. Check the results and optimization suggestions

### 2. Via API

```bash
curl -X POST "http://localhost:8000/api/migrations/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "source_sql": "SELECT NOW(), COUNT(*) FROM `users`",
    "source_dialect": "mysql",
    "target_dialect": "snowflake",
    "optimization_level": "standard"
  }'
```

### 3. Compare Results

Try the same SQL with and without the API key configured to see the quality difference.

## Best Practices

1. **Start Simple**: Test with simple queries first
2. **Review Translations**: Always review AI-generated SQL before production use
3. **Use Schema Context**: Provide table schemas for more accurate translations
4. **Batch Wisely**: Stay within rate limits by batching large migrations
5. **Monitor Logs**: Check logs to ensure API is being used
6. **Cache Results**: Consider caching translations for repeated queries

## Advanced Configuration

### Custom Generation Settings

The translator uses these optimized settings:
```python
generation_config = {
    "temperature": 0.1,      # Low for consistent output
    "top_p": 0.95,           # Focused probability distribution
    "top_k": 40,             # Consider top 40 tokens
    "max_output_tokens": 8192  # Support large SQL schemas
}
```

### Optimization Levels

- **Basic**: Simple dialect conversion, no optimizations
- **Standard**: Applies best practices and basic optimizations
- **Aggressive**: Full performance optimization with clustering/partitioning suggestions

## Support & Resources

- **Google AI Studio**: https://aistudio.google.com
- **Gemini API Docs**: https://ai.google.dev/docs
- **Rate Limits**: https://ai.google.dev/pricing
- **Application Logs**: Check backend logs for detailed translation info

## Next Steps

1. ✅ Get your free Gemini API key
2. ✅ Add it to your `.env` file
3. ✅ Restart the application
4. ✅ Test with a simple SQL query
5. ✅ Enjoy accurate AI-powered translations!
