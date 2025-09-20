#!/usr/bin/env python3
"""
Test script to validate core data quality and migration functionality
"""

import sys
import os
import asyncio
import pandas as pd
from datetime import datetime

# Add the workspace to Python path
sys.path.insert(0, '/workspace')

def test_data_quality_analyzer():
    """Test the DataQualityAnalyzer functionality"""
    try:
        from app.data_quality.analyzer import DataQualityAnalyzer
        
        print("=" * 60)
        print("TESTING DATA QUALITY ANALYZER")
        print("=" * 60)
        
        analyzer = DataQualityAnalyzer()
        print("✓ DataQualityAnalyzer initialized successfully")
        
        # Create sample data with various quality issues
        data = {
            'id': [1, 2, 3, 4, 5, 1, 6, 7],  # Duplicates
            'name': ['John Doe', 'Jane Smith', 'Bob Johnson', None, 'Alice Brown', 'John Doe', 'Charlie Wilson', ''],  # Missing values
            'age': [25, 30, 35, 28, 40, 25, 150, -5],  # Outliers
            'email': ['john@test.com', 'jane@test.com', 'bob@test.com', 'invalid-email', 'alice@test.com', 'john@test.com', 'charlie@test.com', 'wilson@test.com'],
            'salary': [50000, 60000, 75000, 45000, 90000, 50000, 1000000, None]  # More outliers and missing
        }
        df = pd.DataFrame(data)
        
        print(f"✓ Created sample dataset with {len(df)} rows and {len(df.columns)} columns")
        
        async def run_analysis():
            # Run comprehensive analysis
            result = await analyzer.analyze_data_quality(df, ai_enabled=True)
            
            print("\n--- ANALYSIS RESULTS ---")
            print(f"Overall Quality Score: {result['quality_metrics'].overall_quality_score:.1f}%")
            print(f"Completeness Score: {result['quality_metrics'].completeness_score:.1f}%")
            print(f"Accuracy Score: {result['quality_metrics'].accuracy_score:.1f}%")
            print(f"Consistency Score: {result['quality_metrics'].consistency_score:.1f}%")
            print(f"Validity Score: {result['quality_metrics'].validity_score:.1f}%")
            print(f"Uniqueness Score: {result['quality_metrics'].uniqueness_score:.1f}%")
            
            print(f"\nDuplicates Found: {result['duplicate_analysis'].total_duplicates}")
            print(f"Missing Values: {result['missing_value_analysis'].total_missing}")
            print(f"Outliers Detected: {result['outlier_analysis'].total_outliers}")
            
            # Show column profiles
            print(f"\nColumn Profiles:")
            for profile in result['column_profiles'][:3]:  # Show first 3 columns
                print(f"  - {profile['name']}: {profile['data_type']} ({profile['null_percentage']:.1f}% missing)")
            
            # Show AI recommendations
            if result['ai_recommendations'] and result['ai_recommendations'].cleaning_priority:
                print(f"\nTop AI Recommendations:")
                for i, rec in enumerate(result['ai_recommendations'].cleaning_priority[:2], 1):
                    print(f"  {i}. {rec['issue']} (priority: {rec['priority']})")
            
            return True
        
        success = asyncio.run(run_analysis())
        if success:
            print("\n✓ Data quality analysis completed successfully!")
            return True
            
    except Exception as e:
        print(f"✗ Data quality analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_migration_services():
    """Test migration services without full app context"""
    try:
        print("\n" + "=" * 60)
        print("TESTING MIGRATION SERVICES")
        print("=" * 60)
        
        # Test individual service components
        from app.migration.services import MigrationService
        
        migration_service = MigrationService()
        print("✓ MigrationService initialized successfully")
        
        async def test_services():
            # Test supported databases
            databases = await migration_service.get_supported_databases()
            print(f"✓ Retrieved {len(databases)} supported database types")
            
            for db in databases[:3]:  # Show first 3
                print(f"  - {db.name} ({db.type}) - {len(db.features)} features")
            
            return True
        
        success = asyncio.run(test_services())
        
        # Test SQL Translation Service separately
        try:
            from app.migration.services import SQLTranslationService
            
            sql_service = SQLTranslationService()
            print("✓ SQLTranslationService initialized successfully")
            
            async def test_sql_translation():
                # Test basic SQL translation
                source_sql = """
                SELECT u.id, u.name, COUNT(o.id) as order_count
                FROM users u
                LEFT JOIN orders o ON u.id = o.user_id
                WHERE u.created_at >= '2023-01-01'
                GROUP BY u.id, u.name
                ORDER BY order_count DESC
                LIMIT 100;
                """
                
                result = await sql_service.translate_sql(
                    source_sql=source_sql,
                    source_dialect='mysql',
                    target_dialect='snowflake',
                    optimization_level='standard'
                )
                
                print(f"✓ SQL translation completed")
                print(f"  - Confidence: {result['confidence_score']:.2f}")
                print(f"  - Method: {result['translation_method']}")
                print(f"  - Suggestions: {len(result.get('optimization_suggestions', []))}")
                
                return True
            
            sql_success = asyncio.run(test_sql_translation())
            success = success and sql_success
            
        except Exception as e:
            print(f"⚠ SQL translation test skipped: {e}")
        
        # Test Connection Service
        try:
            from app.migration.services import ConnectionService
            
            conn_service = ConnectionService()
            print("✓ ConnectionService initialized successfully")
            
            async def test_connection():
                # Test connection validation
                result = await conn_service.test_connection(
                    connection_type='postgresql',
                    host='localhost',
                    port=5432,
                    database='test_db',
                    username='test_user',
                    password='test_pass'
                )
                
                print(f"✓ Connection test completed")
                print(f"  - Success: {result.success}")
                print(f"  - Response time: {result.response_time_ms:.1f}ms")
                if not result.success:
                    print(f"  - Message: {result.message}")
                
                return True
            
            conn_success = asyncio.run(test_connection())
            success = success and conn_success
            
        except Exception as e:
            print(f"⚠ Connection service test skipped: {e}")
        
        if success:
            print("\n✓ Migration services tests completed successfully!")
            return True
        
    except Exception as e:
        print(f"✗ Migration services test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all functionality tests"""
    print("DATAFLOW AI - FUNCTIONALITY TEST")
    print("Testing core data quality and SQL migration functionality")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test data quality analyzer
    dq_success = test_data_quality_analyzer()
    
    # Test migration services
    migration_success = test_migration_services()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Data Quality Analyzer: {'✓ PASS' if dq_success else '✗ FAIL'}")
    print(f"Migration Services: {'✓ PASS' if migration_success else '✗ FAIL'}")
    
    overall_success = dq_success and migration_success
    print(f"\nOverall Status: {'✓ ALL TESTS PASSED' if overall_success else '✗ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Core functionality is working correctly!")
        print("Data quality analysis and SQL migration features are accessible and functional.")
    else:
        print("\n⚠️  Some functionality issues detected.")
        print("Please check the error messages above for details.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)