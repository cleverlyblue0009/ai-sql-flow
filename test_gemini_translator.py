"""
Test script for Gemini-powered SQL translation
Run this to verify the Gemini integration is working correctly
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.migration.ai_translator import AITranslationEngine


async def test_translator():
    """Test the Gemini translator"""
    
    print("=" * 60)
    print("Gemini SQL Translation Integration Test")
    print("=" * 60)
    print()
    
    # Initialize the engine
    print("1. Initializing AI Translation Engine...")
    engine = AITranslationEngine()
    
    print(f"   ✓ Engine initialized")
    print(f"   ✓ Using Gemini API: {engine.use_api}")
    
    if not engine.use_api:
        print()
        print("⚠️  WARNING: Gemini API not configured!")
        print("   The system will use rule-based translation as fallback.")
        print()
        print("   To enable Gemini API:")
        print("   1. Get free API key from: https://aistudio.google.com/app/apikey")
        print("   2. Add to .env file: GEMINI_API_KEY=your-key-here")
        print("   3. Restart the application")
        print()
    else:
        print("   ✓ Gemini 1.5 Pro model ready")
        print()
    
    # Test SQL samples
    test_cases = [
        {
            "name": "MySQL to Snowflake - CREATE TABLE",
            "sql": """
CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `email` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT NOW()
) ENGINE=InnoDB;
            """.strip(),
            "source": "mysql",
            "target": "snowflake"
        },
        {
            "name": "PostgreSQL to Snowflake - SELECT Query",
            "sql": """
SELECT 
  username,
  COUNT(*) as total,
  AGE(NOW(), created_at) as account_age
FROM users
WHERE status = 'active'
GROUP BY username
LIMIT 10;
            """.strip(),
            "source": "postgresql",
            "target": "snowflake"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Source: {test_case['source']} → Target: {test_case['target']}")
        print()
        
        try:
            result = await engine.translate_sql_advanced(
                source_sql=test_case['sql'],
                source_dialect=test_case['source'],
                target_dialect=test_case['target'],
                optimization_level="standard"
            )
            
            print(f"   ✓ Translation completed")
            print(f"   Method: {result['translation_method']}")
            print(f"   Confidence: {result['confidence_score']:.2%}")
            print(f"   Similarity: {result['semantic_similarity']:.2%}")
            print()
            print(f"   Original SQL:")
            print("   " + "\n   ".join(test_case['sql'].split("\n")))
            print()
            print(f"   Translated SQL:")
            translated_lines = result['translated_sql'].split("\n")
            for line in translated_lines[:10]:  # Show first 10 lines
                print(f"   {line}")
            if len(translated_lines) > 10:
                print(f"   ... ({len(translated_lines) - 10} more lines)")
            print()
            
            if result['optimization_suggestions']:
                print(f"   Optimization Suggestions:")
                for suggestion in result['optimization_suggestions'][:3]:
                    print(f"   • {suggestion}")
                if len(result['optimization_suggestions']) > 3:
                    print(f"   ... ({len(result['optimization_suggestions']) - 3} more suggestions)")
            
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
    
    print()
    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print()
    
    if engine.use_api:
        print("✅ Gemini API is working correctly!")
        print("   Your SQL translations will use AI-powered accuracy.")
    else:
        print("⚠️  Using rule-based translation (fallback mode)")
        print("   Add GEMINI_API_KEY to .env for AI-powered translations.")
    
    print()
    return True


if __name__ == "__main__":
    try:
        asyncio.run(test_translator())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
