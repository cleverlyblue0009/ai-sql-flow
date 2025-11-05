# SQL File Type Detection Fix - Issue Resolution

## Problem
The SQL converter was failing with a 422 (Unprocessable Entity) error when trying to convert SQL files. The error occurred at the `/migration/convert-sql-batch` endpoint because FastAPI couldn't properly validate the request body.

## Root Cause
The `/convert-sql-batch` endpoint in `app/migration/routes.py` was defined with raw function parameters instead of using a Pydantic schema:

```python
# OLD - Problematic code
async def convert_sql_batch(
    files: List[Dict[str, Any]],
    target_dialect: str,
    conversion_options: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
```

FastAPI with direct parameters like this can have issues with complex request body validation, especially with nested structures.

## Solution
Added proper Pydantic schemas for request/response validation and updated the endpoint to use them:

### 1. Created New Schemas (`app/migration/schemas.py`)

```python
class SQLFileInput(BaseModel):
    filename: str
    content: str
    source_dialect: Optional[str] = None

class BatchConversionOptions(BaseModel):
    optimization_level: Optional[str] = "standard"
    convert_schema: Optional[bool] = True
    convert_data: Optional[bool] = True
    keep_constraints: Optional[bool] = True
    optimize_code: Optional[bool] = True

class BatchSQLConversionRequest(BaseModel):
    files: List[SQLFileInput]
    target_dialect: str
    conversion_options: Optional[BatchConversionOptions] = None

class BatchSQLConversionResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]

class DialectDetectionRequest(BaseModel):
    sql_content: str
    filename: Optional[str] = "unknown.sql"

class DialectDetectionResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
```

### 2. Updated Endpoints (`app/migration/routes.py`)

**Convert SQL Batch Endpoint:**
```python
@router.post("/convert-sql-batch", response_model=BatchSQLConversionResponse)
async def convert_sql_batch(
    request: BatchSQLConversionRequest,
    db: Session = Depends(get_db)
):
    # Convert to dict format for batch_converter
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
    
    result = await batch_converter.convert_batch(
        files=files_data,
        target_dialect=request.target_dialect,
        conversion_options=conversion_options
    )
    
    return BatchSQLConversionResponse(
        success=True,
        message=f"Converted {result['success_count']} files successfully",
        data=result
    )
```

**Detect Dialect Endpoint:**
```python
@router.post("/detect-dialect", response_model=DialectDetectionResponse)
async def detect_sql_dialect(
    request: DialectDetectionRequest
):
    result = await batch_converter.detect_sql_dialect(
        request.sql_content, 
        request.filename or "unknown.sql"
    )
    return DialectDetectionResponse(
        success=True,
        data=result
    )
```

## Benefits

1. **Proper Request Validation**: FastAPI now properly validates all request fields with type checking
2. **Better Error Messages**: If validation fails, FastAPI provides clear error messages about what's wrong
3. **Type Safety**: Full type hints throughout the request/response cycle
4. **Auto-generated Documentation**: OpenAPI/Swagger docs are now accurate and complete
5. **Consistent Response Format**: All responses follow the same structure

## Testing

The frontend code in `SQLConverterWizard.tsx` already sends the request in the correct format:

```javascript
const response = await fetch('http://localhost:8000/migration/convert-sql-batch', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    files: filesData,
    target_dialect: targetDB,
    conversion_options: {
      optimization_level: conversionOptions.optimizeCode ? 'standard' : 'basic',
      convert_schema: conversionOptions.convertSchema,
      convert_data: conversionOptions.convertData,
      keep_constraints: conversionOptions.keepConstraints,
      optimize_code: conversionOptions.optimizeCode
    }
  })
});
```

This request format now matches the Pydantic schema exactly, so validation will succeed.

## Files Modified

1. `app/migration/schemas.py` - Added new schemas for batch conversion
2. `app/migration/routes.py` - Updated endpoints to use new schemas

## Next Steps

To test the fix:
1. Restart the backend server
2. Upload SQL files in the SQL Converter UI
3. The conversion should now work without the 422 error

## Expected Behavior After Fix

✅ Request validation succeeds
✅ File type detection works correctly
✅ SQL conversion processes successfully
✅ Proper error messages if something does go wrong
✅ Download of converted files works
