# SQL Converter - Quick Start Guide

## 🚀 Getting Started

The new SQL Converter wizard makes it incredibly easy to convert SQL files between different database dialects. Follow these simple steps:

---

## 📋 Prerequisites

### Required
- Python 3.8+ with FastAPI backend running
- Node.js 16+ with frontend running

### Optional (for best results)
- **Google Gemini API Key**: For AI-powered dialect detection
  - Set in backend: `GEMINI_API_KEY` or `GOOGLE_API_KEY`
  - Without API key: Falls back to rule-based detection (still works!)

---

## 🎯 Using the SQL Converter (4 Easy Steps)

### Step 1: Upload & Auto-Detect ⬆️

1. Navigate to **SQL Migration** in the sidebar
2. **Drag and drop** your SQL files (or click to browse)
   - Supported: `.sql`, `.ddl` files (up to 50MB each)
3. Watch as files are **automatically analyzed**:
   - Source dialect detected (MySQL, PostgreSQL, SQL Server, etc.)
   - Confidence score displayed (0-100%)
   - Color-coded indicators:
     - 🟢 Green: High confidence (≥80%)
     - 🟡 Yellow: Medium confidence (50-80%)
     - 🔴 Red: Low confidence (<50%)

**💡 Pro Tip:** If confidence is low, you can manually override the detected dialect!

---

### Step 2: Configure Conversion ⚙️

1. **Select Target Database**:
   - Choose from: MySQL, PostgreSQL, SQL Server, Oracle, Snowflake, SQLite
   
2. **Customize Conversion Options** (all enabled by default):
   - ✓ Convert table structure
   - ✓ Convert data queries
   - ✓ Keep constraints
   - ✓ Optimize code
   - ✓ Add migration comments

3. Review the **Source Database Summary**:
   - See which dialects were detected
   - View file counts per dialect
   - Check average confidence scores

Click **"Review & Execute"** when ready →

---

### Step 3: Review & Execute ⚡

1. **Review Conversion Summary**:
   - Number of files to convert
   - Target database
   - Estimated processing time

2. **Click "Start Conversion"**:
   - Watch the real-time progress bar
   - See files being processed
   - Wait for completion (typically 2-5 seconds per file)

---

### Step 4: Download & Analytics 📊

**Congratulations! Your conversion is complete!** 🎉

#### Download Options:
1. **Download All as ZIP**: 
   - Contains all converted files
   - Includes detailed conversion report
   - One-click download
   
2. **Download Individual Files**:
   - Click download button on any file
   - Gets clean, formatted SQL
   
3. **Download Report Only**:
   - Markdown report with full details
   - Perfect for documentation

#### View Analytics:
- **Success Summary**: Files converted, confidence, processing time
- **Individual File Results**:
  - Translation confidence per file
  - Line count changes (before → after)
  - Warnings and optimization suggestions
  - Processing time per file

---

## 📝 Example Workflow

### Converting MySQL to Snowflake

```
1. Upload Files:
   - users.sql (MySQL, 95% confidence) ✅
   - orders.sql (MySQL, 88% confidence) ✅
   - products.sql (MySQL, 65% confidence) ⚠️

2. Configure:
   - Target: Snowflake ❄️
   - Options: All enabled ✓

3. Execute:
   - Processing... [████████░░] 80%
   - Completed in 4.2 seconds ✅

4. Download:
   - translated_users.sql
   - translated_orders.sql
   - translated_products.sql
   - conversion_report.md
   - [Download as ZIP] 📦
```

---

## 🎨 Output Format

Your converted files will look like this:

```sql
-- ============================================================
-- SQL Translation Report
-- ============================================================
-- Original File: users.sql
-- Source Database: MYSQL
-- Target Database: SNOWFLAKE
-- Detection Confidence: 95%
-- Generated: 2025-11-05 15:42:30
-- Translator: DataFlow AI SQL Converter
-- ============================================================

CREATE TABLE users (
  user_id INT AUTOINCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  email VARCHAR(100) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  UNIQUE (email)
);

-- ============================================================
-- Optimization Suggestions
-- ============================================================
-- 1. Consider adding clustering keys for better performance
-- 2. Review indexing strategy for frequently accessed columns
-- 3. Use Snowflake's micro-partitioning on created_at
-- ============================================================
```

**Clean, professional, ready-to-use!**

---

## 🔧 Advanced Features

### Manual Dialect Override
If auto-detection fails or shows low confidence:
1. Click the dropdown next to the detected dialect
2. Select the correct source database
3. Confidence will update to 100%

### Batch Processing
- Upload **multiple files at once** (up to 50MB each)
- All files processed **in parallel** (not sequential)
- Real-time status for each file

### Error Handling
- Files with errors don't block other files
- Clear error messages per file
- Warnings shown but conversion proceeds

---

## 💡 Tips for Best Results

### 1. **File Preparation**
- Remove comments if they cause confusion
- Ensure SQL is syntactically valid
- Split very large files (>10MB) for faster processing

### 2. **Confidence Scores**
- **>80%**: Proceed with confidence ✅
- **50-80%**: Review output carefully ⚠️
- **<50%**: Use manual override or review SQL 🔴

### 3. **Post-Conversion**
- **Always review** converted SQL before production use
- **Test queries** in target database
- **Read optimization suggestions** for performance tips
- **Check warnings** for potential issues

### 4. **Common Issues**
- **Low confidence**: Add more dialect-specific syntax
- **Large files**: May take longer, be patient
- **API errors**: Falls back to rule-based detection automatically

---

## 🆘 Troubleshooting

### "No dialect detected (unknown)"
**Solution:** 
- File may not contain dialect-specific syntax
- Manually select source database
- Add more SQL statements for better detection

### "Conversion failed"
**Solution:**
- Check if SQL is syntactically valid
- Review error message in file results
- Try converting in smaller batches

### "Low confidence warning"
**Solution:**
- Use manual dialect override
- Review and verify converted SQL
- Add more dialect-specific features to source SQL

---

## 📚 Supported Databases

| Source | Target | Status |
|--------|--------|--------|
| MySQL | All | ✅ Excellent |
| PostgreSQL | All | ✅ Excellent |
| SQL Server | All | ✅ Excellent |
| Oracle | All | ✅ Good |
| Snowflake | All | ✅ Good |
| SQLite | All | ✅ Good |

---

## 🎯 Next Steps

1. **Start Converting**: Navigate to SQL Migration and upload your first file!
2. **Review Documentation**: Read the full [SQL_CONVERTER_OVERHAUL_COMPLETE.md](./SQL_CONVERTER_OVERHAUL_COMPLETE.md)
3. **Provide Feedback**: Let us know how the new converter works for you!

---

## 📞 Support

- **Questions?** Check the troubleshooting section
- **Issues?** Review error messages and logs
- **Feature Requests?** We'd love to hear your ideas!

---

**Happy Converting! 🚀**

*Made with ❤️ by DataFlow AI*
