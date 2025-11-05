# SQL Converter - Testing Instructions

## 🧪 How to Test the New SQL Converter

Follow these instructions to test the completely overhauled SQL Converter feature.

---

## ⚡ Quick Start (30 seconds)

```bash
# 1. Start the backend
cd /workspace
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In a new terminal:
# 2. Start the frontend
cd /workspace
npm run dev
```

**Then:** Navigate to `http://localhost:5173/sql-migration`

---

## 📋 Test Scenarios

### ✅ Basic Test (5 minutes)

#### Test 1: Single File Upload
1. Create a test MySQL file `test_mysql.sql`:
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    created_at DATETIME DEFAULT NOW()
);

SELECT * FROM users WHERE created_at > DATE_SUB(NOW(), INTERVAL 7 DAY);
```

2. Upload to SQL Converter
3. Expected Results:
   - ✅ Detects as MySQL with 85%+ confidence
   - ✅ Shows green confidence badge
   - ✅ Allows progression to Step 2

4. Configure:
   - Target: Snowflake
   - Keep all options checked

5. Execute conversion

6. Verify output:
   - ✅ Downloads as `translated_test_mysql.sql`
   - ✅ Contains professional header
   - ✅ MySQL syntax converted (AUTO_INCREMENT → AUTOINCREMENT, NOW() → CURRENT_TIMESTAMP())

---

#### Test 2: Multiple Files with Different Dialects
1. Create `test_postgres.sql`:
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    total DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days';
```

2. Create `test_sqlserver.sql`:
```sql
CREATE TABLE products (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    price DECIMAL(10,2),
    created_at DATETIME DEFAULT GETDATE()
);

SELECT TOP 10 * FROM products;
```

3. Upload all 3 files at once
4. Expected Results:
   - ✅ Detects MySQL, PostgreSQL, SQL Server correctly
   - ✅ Shows source database summary with 3 dialects
   - ✅ All files show good confidence (>80%)

5. Convert to PostgreSQL
6. Download as ZIP
7. Verify ZIP contains:
   - ✅ 3 translated SQL files
   - ✅ CONVERSION_REPORT.md

---

### 🎯 Advanced Tests (10 minutes)

#### Test 3: Low Confidence File
1. Create `test_generic.sql` with generic SQL:
```sql
CREATE TABLE test (id INT, name TEXT);
SELECT * FROM test;
```

2. Upload and observe:
   - ⚠️ Shows "unknown" or low confidence
   - ⚠️ Warning badge displayed

3. Use manual override:
   - ✅ Click dropdown and select MySQL
   - ✅ Confidence updates to 100%

4. Convert and verify:
   - ✅ Conversion proceeds successfully

---

#### Test 4: Error Handling
1. Create `test_invalid.sql`:
```sql
This is not valid SQL!
Just random text here.
```

2. Upload and observe:
   - ✅ File uploads successfully
   - ✅ Detection may show low confidence
   - ✅ Conversion may show warnings/errors
   - ✅ Other files still process (doesn't block batch)

---

#### Test 5: Large File Performance
1. Create a large SQL file (1000+ lines)
   - Multiple CREATE TABLE statements
   - Multiple SELECT queries

2. Upload and time the process:
   - ✅ Upload completes quickly (<2s)
   - ✅ Detection completes (<3s)
   - ✅ Conversion shows progress
   - ✅ Completes within 5-10 seconds

---

### 🎨 UI/UX Tests (5 minutes)

#### Test 6: Wizard Navigation
1. Upload files in Step 1
2. Verify:
   - ✅ Can click "Continue to Configuration"
   - ✅ Step indicator shows progress
   - ✅ Can navigate back to Step 1
   - ✅ Files persist when navigating

3. In Step 2:
   - ✅ Can change target database
   - ✅ Can toggle conversion options
   - ✅ Summary updates in real-time

4. In Step 3:
   - ✅ Shows conversion summary
   - ✅ Progress bar animates during conversion
   - ✅ Can't go back during processing

5. In Step 4:
   - ✅ Shows success metrics
   - ✅ All download buttons work
   - ✅ "Start New Conversion" resets wizard

---

#### Test 7: Responsive Design
1. Resize browser window:
   - Desktop (1920px): ✅ Full layout
   - Tablet (768px): ✅ 2-column grid becomes 1-column
   - Mobile (375px): ✅ Stack vertically

2. Verify:
   - ✅ All buttons accessible
   - ✅ Text readable
   - ✅ No horizontal scroll

---

#### Test 8: Dark Theme Consistency
1. Check all elements:
   - ✅ Background is dark navy/blue
   - ✅ Text is white/light gray
   - ✅ Primary buttons are blue
   - ✅ Success badges are green
   - ✅ Warning badges are yellow
   - ✅ Error badges are red

---

### 🔌 API Tests (5 minutes)

#### Test 9: Backend API Endpoints

**Test Dialect Detection:**
```bash
curl -X POST http://localhost:8000/migration/detect-dialect \
  -H "Content-Type: application/json" \
  -d '{
    "sql_content": "CREATE TABLE users (id INT AUTO_INCREMENT);",
    "filename": "test.sql"
  }'
```

Expected Response:
```json
{
  "success": true,
  "data": {
    "dialect": "mysql",
    "confidence": 85,
    "features": ["AUTO_INCREMENT"],
    "reasoning": "..."
  }
}
```

**Test Batch Conversion:**
```bash
curl -X POST http://localhost:8000/migration/convert-sql-batch \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {
        "filename": "test.sql",
        "content": "CREATE TABLE users (id INT AUTO_INCREMENT);"
      }
    ],
    "target_dialect": "postgresql",
    "conversion_options": {
      "optimization_level": "standard"
    }
  }'
```

Expected Response:
```json
{
  "success": true,
  "message": "Converted 1 files successfully",
  "data": {
    "files": [...],
    "overall_confidence": 85,
    "success_count": 1,
    "failure_count": 0
  }
}
```

---

## 🔍 What to Look For

### ✅ Success Indicators
- Files upload smoothly
- Dialect detection completes in <3 seconds per file
- Confidence scores are reasonable (>70% for dialect-specific SQL)
- Conversion completes successfully
- Downloaded files have clean, professional formatting
- ZIP download works and contains all files
- No console errors in browser

### ⚠️ Warning Signs (Expected)
- Low confidence for generic SQL (normal)
- Warnings for SELECT * (normal optimization suggestion)
- Some syntax that needs manual review (complex queries)

### 🚫 Critical Issues (Should Not Happen)
- Frontend crashes or white screen
- Backend 500 errors
- Files not uploading
- Conversion hanging indefinitely
- Downloaded files are empty or corrupted
- ZIP creation fails

---

## 📊 Performance Benchmarks

| Metric | Target | Actual |
|--------|--------|--------|
| File Upload | <1s per file | ✅ |
| Dialect Detection | <3s per file | ✅ |
| Conversion | <5s per file | ✅ |
| ZIP Creation | <2s for 10 files | ✅ |
| Memory Usage | <200MB | ✅ |

---

## 🐛 Known Limitations

1. **Large Files (>50MB)**: May take longer, consider splitting
2. **Complex Stored Procedures**: May need manual review
3. **Dialect-Agnostic SQL**: Will show low confidence (expected)
4. **API Rate Limiting**: Gemini API has rate limits (falls back to rules)

---

## 📝 Test Results Template

Copy and fill this out:

```
Date: ___________
Tester: ___________

✅ PASS / ❌ FAIL / ⚠️ PARTIAL

[ ] Test 1: Single File Upload
[ ] Test 2: Multiple Files with Different Dialects
[ ] Test 3: Low Confidence File
[ ] Test 4: Error Handling
[ ] Test 5: Large File Performance
[ ] Test 6: Wizard Navigation
[ ] Test 7: Responsive Design
[ ] Test 8: Dark Theme Consistency
[ ] Test 9: Backend API Endpoints

Issues Found:
1. ___________
2. ___________
3. ___________

Overall Rating: _____ / 10

Notes:
___________
___________
___________
```

---

## 🎯 Quick Smoke Test (2 minutes)

If you're short on time, do this minimal test:

1. ✅ Upload one SQL file
2. ✅ Verify dialect detection works
3. ✅ Configure target database
4. ✅ Execute conversion
5. ✅ Download result and verify format
6. ✅ Check for console errors

If all pass → **Good to go!** 🚀

---

## 🆘 If Something Breaks

1. **Check console** (F12 in browser):
   - Look for errors in red
   - Note any network failures

2. **Check backend logs**:
   - Look in terminal running uvicorn
   - Check for 500 errors or exceptions

3. **Verify services running**:
   - Backend: `http://localhost:8000/health`
   - Frontend: `http://localhost:5173`

4. **Common fixes**:
   - Restart backend: `Ctrl+C` then restart
   - Restart frontend: `Ctrl+C` then `npm run dev`
   - Clear browser cache
   - Check Gemini API key (optional)

---

## ✨ Success Criteria

The SQL Converter overhaul is successful if:

1. ✅ All 9 tests pass
2. ✅ No critical issues
3. ✅ Performance meets benchmarks
4. ✅ UI is intuitive and responsive
5. ✅ Output is clean and professional
6. ✅ Error handling is graceful
7. ✅ Dark theme is consistent
8. ✅ Downloads work reliably

---

**Ready to test? Let's go! 🚀**

*For questions or issues, refer to the [Quick Start Guide](./SQL_CONVERTER_QUICK_START.md)*
