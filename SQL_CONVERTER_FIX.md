# SQL Converter 422 Error Fix

## Problem
The SQL Converter Wizard was failing with a 422 (Unprocessable Entity) error when trying to convert SQL files. The error occurred because:

1. **Missing Pydantic schemas**: The backend endpoints were using raw parameters instead of proper Pydantic models
2. **Type validation failure**: FastAPI couldn't validate the request body structure
3. **Inconsistent parameter handling**: The endpoints weren't properly structured for request body parsing

## Solution Implemented

### 1. Created New Pydantic Schemas (`app/migration/schemas.py`)

Added three new schemas for proper request validation:

```python
class SQLFileInput(BaseModel):
    """Input for a single SQL file in batch conversion"""
    filename: str
    content: str
    source_dialect: Optional[str] = None


class BatchConversionOptions(BaseModel):
    """Options for batch SQL conversion"""
    optimization_level: str = "standard"
    convert_schema: bool = True
    convert_data: bool = True
    keep_constraints: bool = True
    optimize_code: bool = True


class BatchSQLConversionRequest(BaseModel):
    """Request for batch SQL conversion"""
    files: List[SQLFileInput]
    target_dialect: str
    conversion_options: Optional[BatchConversionOptions] = None


class SQLDialectDetectionRequest(BaseModel):
    """Request for SQL dialect detection"""
    sql_content: str
    filename: str = "unknown.sql"
```

### 2. Updated Backend Endpoints (`app/migration/routes.py`)

#### Before:
```python
@router.post("/convert-sql-batch")
async def convert_sql_batch(
    files: List[Dict[str, Any]],
    target_dialect: str,
    conversion_options: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
```

#### After:
```python
@router.post("/convert-sql-batch")
async def convert_sql_batch(
    request: BatchSQLConversionRequest
):
```

#### Before:
```python
@router.post("/detect-dialect")
async def detect_sql_dialect(
    sql_content: str,
    filename: str = "unknown.sql"
):
```

#### After:
```python
@router.post("/detect-dialect")
async def detect_sql_dialect(
    request: SQLDialectDetectionRequest
):
```

### 3. Added Proper Request Body Parsing

The endpoints now properly convert Pydantic models to dictionaries before passing to the converter:

```python
# Convert Pydantic models to dicts for processing
files_data = [
    {
        "filename": file.filename,
        "content": file.content,
        "source_dialect": file.source_dialect
    }
    for file in request.files
]

conversion_options = {}
if request.conversion_options:
    conversion_options = request.conversion_options.dict()
```

## How to Apply the Fix

### Option 1: Restart Backend (Recommended)
If the backend is running with auto-reload (development mode):
```bash
# The changes should auto-reload
# If not, restart manually:
cd /workspace
./scripts/start.sh dev
```

### Option 2: Using Docker
```bash
cd /workspace
docker-compose restart api
```

## Testing the Fix

1. **Upload SQL files** in the SQL Converter Wizard
2. **Auto-detect** the source database dialect
3. **Configure** target database and options
4. **Execute conversion** - should now work without 422 errors

## What Was Fixed

✅ **Proper request validation** - FastAPI can now validate request bodies
✅ **Type safety** - All parameters are properly typed with Pydantic models
✅ **Better error messages** - Validation errors will now show specific field issues
✅ **Consistent API structure** - All conversion endpoints follow the same pattern

## Expected Behavior

### Successful Request:
```json
{
  "files": [
    {
      "filename": "script.sql",
      "content": "CREATE TABLE users...",
      "source_dialect": "mysql"
    }
  ],
  "target_dialect": "snowflake",
  "conversion_options": {
    "optimization_level": "standard",
    "convert_schema": true,
    "convert_data": true,
    "keep_constraints": true,
    "optimize_code": true
  }
}
```

### Successful Response:
```json
{
  "success": true,
  "message": "Converted 1 files successfully",
  "data": {
    "files": [...],
    "overall_confidence": 85.5,
    "total_processing_time_ms": 2500,
    "success_count": 1,
    "failure_count": 0
  }
}
```

## Files Modified

1. `/workspace/app/migration/schemas.py` - Added new schemas
2. `/workspace/app/migration/routes.py` - Updated endpoints to use schemas

## No Breaking Changes

The frontend code in `SQLConverterWizard.tsx` already sends data in the correct format, so no frontend changes are needed. The fix only makes the backend properly parse the requests.

---

**Status**: ✅ Fixed and ready to use after backend restart
**Date**: 2025-11-05
**Impact**: Resolves 422 errors in SQL conversion workflow
