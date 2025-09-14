"""
SQL Parser and Schema Analysis Module
Provides comprehensive SQL parsing, schema extraction, and analysis capabilities
"""

import re
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlparse
from sqlparse.sql import Statement, IdentifierList, Identifier, Function
from sqlparse.tokens import Keyword, DML, DDL

logger = logging.getLogger(__name__)


class SQLObjectType(Enum):
    TABLE = "table"
    VIEW = "view"
    INDEX = "index"
    TRIGGER = "trigger"
    PROCEDURE = "procedure"
    FUNCTION = "function"
    SEQUENCE = "sequence"


class SQLOperation(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
    ALTER = "ALTER"
    DROP = "DROP"
    TRUNCATE = "TRUNCATE"


@dataclass
class ColumnInfo:
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    default_value: Optional[str] = None
    constraints: List[str] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []


@dataclass
class TableInfo:
    name: str
    schema: Optional[str] = None
    columns: List[ColumnInfo] = None
    indexes: List[str] = None
    constraints: List[str] = None
    table_type: str = "TABLE"
    
    def __post_init__(self):
        if self.columns is None:
            self.columns = []
        if self.indexes is None:
            self.indexes = []
        if self.constraints is None:
            self.constraints = []


@dataclass
class SQLAnalysisResult:
    """Comprehensive SQL analysis result"""
    tables: List[TableInfo]
    operations: List[SQLOperation]
    schemas: Set[str]
    complexity_score: int
    line_count: int
    statement_count: int
    warnings: List[str]
    suggestions: List[str]
    estimated_execution_time: str
    compatibility_issues: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]


class SQLParser:
    """Advanced SQL parser with schema analysis capabilities"""
    
    def __init__(self):
        self.dialect_keywords = {
            'mysql': {
                'AUTO_INCREMENT', 'TINYINT', 'MEDIUMINT', 'BIGINT', 'LONGTEXT',
                'MEDIUMTEXT', 'TINYTEXT', 'ENUM', 'SET', 'YEAR'
            },
            'postgresql': {
                'SERIAL', 'BIGSERIAL', 'SMALLSERIAL', 'BOOLEAN', 'BYTEA',
                'INET', 'CIDR', 'MACADDR', 'UUID', 'JSON', 'JSONB'
            },
            'sqlserver': {
                'IDENTITY', 'NVARCHAR', 'NCHAR', 'NTEXT', 'DATETIME2',
                'DATETIMEOFFSET', 'UNIQUEIDENTIFIER', 'HIERARCHYID'
            },
            'snowflake': {
                'VARIANT', 'OBJECT', 'ARRAY', 'GEOGRAPHY', 'AUTOINCREMENT',
                'TIMESTAMP_TZ', 'TIMESTAMP_LTZ', 'TIMESTAMP_NTZ'
            },
            'oracle': {
                'NUMBER', 'VARCHAR2', 'NVARCHAR2', 'CLOB', 'NCLOB', 'BLOB',
                'BFILE', 'ROWID', 'UROWID', 'XMLTYPE', 'TIMESTAMP'
            }
        }
    
    def analyze_sql(self, sql_content: str, source_dialect: str = 'mysql') -> SQLAnalysisResult:
        """
        Perform comprehensive SQL analysis
        """
        try:
            # Clean and prepare SQL
            cleaned_sql = self._clean_sql(sql_content)
            
            # Parse SQL statements
            statements = sqlparse.parse(cleaned_sql)
            
            # Initialize analysis components
            tables = []
            operations = []
            schemas = set()
            warnings = []
            suggestions = []
            compatibility_issues = []
            dependencies = {}
            
            # Analyze each statement
            for stmt in statements:
                if stmt.ttype is None:  # Skip empty statements
                    stmt_analysis = self._analyze_statement(stmt, source_dialect)
                    
                    # Collect operations
                    if stmt_analysis.get('operation'):
                        operations.append(stmt_analysis['operation'])
                    
                    # Collect tables and schemas
                    for table in stmt_analysis.get('tables', []):
                        tables.append(table)
                        if table.schema:
                            schemas.add(table.schema)
                    
                    # Collect warnings and suggestions
                    warnings.extend(stmt_analysis.get('warnings', []))
                    suggestions.extend(stmt_analysis.get('suggestions', []))
                    compatibility_issues.extend(stmt_analysis.get('compatibility_issues', []))
                    
                    # Track dependencies
                    if stmt_analysis.get('dependencies'):
                        dependencies.update(stmt_analysis['dependencies'])
            
            # Calculate metrics
            line_count = len([line for line in sql_content.split('\n') if line.strip()])
            statement_count = len([s for s in statements if s.ttype is None])
            complexity_score = self._calculate_complexity(statements, tables, operations)
            
            # Generate additional analysis
            additional_warnings = self._generate_warnings(sql_content, source_dialect)
            additional_suggestions = self._generate_suggestions(operations, tables, complexity_score)
            estimated_time = self._estimate_execution_time(complexity_score, statement_count)
            
            warnings.extend(additional_warnings)
            suggestions.extend(additional_suggestions)
            
            return SQLAnalysisResult(
                tables=tables,
                operations=operations,
                schemas=schemas,
                complexity_score=complexity_score,
                line_count=line_count,
                statement_count=statement_count,
                warnings=list(set(warnings)),  # Remove duplicates
                suggestions=list(set(suggestions)),
                estimated_execution_time=estimated_time,
                compatibility_issues=compatibility_issues,
                dependencies=dependencies
            )
            
        except Exception as e:
            logger.error(f"Error analyzing SQL: {str(e)}")
            # Return basic analysis on error
            return SQLAnalysisResult(
                tables=[],
                operations=[],
                schemas=set(),
                complexity_score=0,
                line_count=len(sql_content.split('\n')),
                statement_count=0,
                warnings=[f"Analysis error: {str(e)}"],
                suggestions=["Manual review recommended due to parsing error"],
                estimated_execution_time="Unknown",
                compatibility_issues=[],
                dependencies={}
            )
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and normalize SQL content"""
        # Remove comments
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # Normalize whitespace
        sql = re.sub(r'\s+', ' ', sql)
        
        return sql.strip()
    
    def _analyze_statement(self, stmt: Statement, dialect: str) -> Dict[str, Any]:
        """Analyze individual SQL statement"""
        analysis = {
            'operation': None,
            'tables': [],
            'warnings': [],
            'suggestions': [],
            'compatibility_issues': [],
            'dependencies': {}
        }
        
        try:
            # Get statement type
            stmt_type = self._get_statement_type(stmt)
            if stmt_type:
                analysis['operation'] = SQLOperation(stmt_type)
            
            # Extract table information
            tables = self._extract_tables(stmt)
            analysis['tables'] = tables
            
            # Check for dialect-specific issues
            compatibility_issues = self._check_compatibility(str(stmt), dialect)
            analysis['compatibility_issues'] = compatibility_issues
            
            # Generate statement-specific warnings
            warnings = self._analyze_statement_warnings(stmt, stmt_type)
            analysis['warnings'] = warnings
            
            # Track dependencies
            if stmt_type in ['CREATE', 'ALTER']:
                deps = self._extract_dependencies(stmt)
                analysis['dependencies'] = deps
            
        except Exception as e:
            logger.warning(f"Error analyzing statement: {str(e)}")
            analysis['warnings'].append(f"Statement analysis warning: {str(e)}")
        
        return analysis
    
    def _get_statement_type(self, stmt: Statement) -> Optional[str]:
        """Extract the main operation type from statement"""
        for token in stmt.flatten():
            if token.ttype in (Keyword, DML, DDL):
                token_value = token.value.upper()
                if token_value in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 
                                 'CREATE', 'ALTER', 'DROP', 'TRUNCATE']:
                    return token_value
        return None
    
    def _extract_tables(self, stmt: Statement) -> List[TableInfo]:
        """Extract table information from statement"""
        tables = []
        
        try:
            # Look for table references in different contexts
            table_patterns = [
                r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'INTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)',
                r'TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)'
            ]
            
            stmt_str = str(stmt).upper()
            
            for pattern in table_patterns:
                matches = re.findall(pattern, stmt_str, re.IGNORECASE)
                for match in matches:
                    if '.' in match:
                        schema, table_name = match.split('.', 1)
                        tables.append(TableInfo(name=table_name.lower(), schema=schema.lower()))
                    else:
                        tables.append(TableInfo(name=match.lower()))
            
            # Remove duplicates
            seen = set()
            unique_tables = []
            for table in tables:
                table_key = f"{table.schema or ''}.{table.name}"
                if table_key not in seen:
                    seen.add(table_key)
                    unique_tables.append(table)
            
            return unique_tables
            
        except Exception as e:
            logger.warning(f"Error extracting tables: {str(e)}")
            return []
    
    def _check_compatibility(self, stmt_str: str, source_dialect: str) -> List[Dict[str, Any]]:
        """Check for dialect-specific compatibility issues"""
        issues = []
        
        try:
            dialect_keywords = self.dialect_keywords.get(source_dialect, set())
            
            for keyword in dialect_keywords:
                if keyword in stmt_str.upper():
                    issues.append({
                        'type': 'dialect_specific',
                        'severity': 'warning',
                        'keyword': keyword,
                        'message': f"'{keyword}' is specific to {source_dialect} and may need translation"
                    })
            
            # Check for common compatibility issues
            if 'LIMIT' in stmt_str.upper() and source_dialect == 'sqlserver':
                issues.append({
                    'type': 'syntax_difference',
                    'severity': 'error',
                    'message': "LIMIT clause not supported in SQL Server, use TOP instead"
                })
            
            if 'TOP' in stmt_str.upper() and source_dialect in ['mysql', 'postgresql']:
                issues.append({
                    'type': 'syntax_difference',
                    'severity': 'warning',
                    'message': "TOP clause may not be supported, consider using LIMIT"
                })
                
        except Exception as e:
            logger.warning(f"Error checking compatibility: {str(e)}")
        
        return issues
    
    def _analyze_statement_warnings(self, stmt: Statement, stmt_type: str) -> List[str]:
        """Generate warnings for specific statement patterns"""
        warnings = []
        stmt_str = str(stmt).upper()
        
        try:
            # Check for SELECT * usage
            if 'SELECT *' in stmt_str:
                warnings.append("SELECT * usage detected - specify column names for better performance")
            
            # Check for missing WHERE clause in UPDATE/DELETE
            if stmt_type in ['UPDATE', 'DELETE'] and 'WHERE' not in stmt_str:
                warnings.append(f"{stmt_type} statement without WHERE clause - this affects all rows")
            
            # Check for potential SQL injection patterns
            if re.search(r"['\"].*\+.*['\"]", stmt_str):
                warnings.append("Potential SQL injection vulnerability - use parameterized queries")
            
            # Check for inefficient patterns
            if 'OR' in stmt_str and 'INDEX' not in stmt_str:
                warnings.append("OR conditions may prevent index usage - consider UNION instead")
            
            if re.search(r'LIKE\s+[\'"]%.*%[\'"]', stmt_str):
                warnings.append("Leading wildcard in LIKE pattern prevents index usage")
                
        except Exception as e:
            logger.warning(f"Error analyzing statement warnings: {str(e)}")
        
        return warnings
    
    def _extract_dependencies(self, stmt: Statement) -> Dict[str, List[str]]:
        """Extract object dependencies from CREATE/ALTER statements"""
        dependencies = {}
        
        try:
            stmt_str = str(stmt).upper()
            
            # Extract foreign key dependencies
            fk_pattern = r'FOREIGN\s+KEY.*REFERENCES\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            fk_matches = re.findall(fk_pattern, stmt_str, re.IGNORECASE)
            if fk_matches:
                dependencies['foreign_keys'] = [match.lower() for match in fk_matches]
            
            # Extract view dependencies
            if 'CREATE VIEW' in stmt_str:
                table_refs = re.findall(r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)', stmt_str, re.IGNORECASE)
                if table_refs:
                    dependencies['view_tables'] = [ref.lower() for ref in table_refs]
                    
        except Exception as e:
            logger.warning(f"Error extracting dependencies: {str(e)}")
        
        return dependencies
    
    def _calculate_complexity(self, statements: List[Statement], tables: List[TableInfo], operations: List[SQLOperation]) -> int:
        """Calculate SQL complexity score"""
        try:
            complexity = 0
            
            # Base complexity from statement count
            complexity += len(statements) * 2
            
            # Add complexity for operations
            operation_weights = {
                SQLOperation.SELECT: 1,
                SQLOperation.INSERT: 2,
                SQLOperation.UPDATE: 3,
                SQLOperation.DELETE: 3,
                SQLOperation.CREATE: 4,
                SQLOperation.ALTER: 5,
                SQLOperation.DROP: 2,
                SQLOperation.TRUNCATE: 2
            }
            
            for op in operations:
                complexity += operation_weights.get(op, 1)
            
            # Add complexity for table count
            complexity += len(tables) * 2
            
            # Add complexity for advanced SQL features
            combined_sql = ' '.join(str(stmt) for stmt in statements).upper()
            
            advanced_features = [
                ('SUBQUERY', 5), ('EXISTS', 4), ('CASE', 3), ('UNION', 4),
                ('INTERSECT', 4), ('EXCEPT', 4), ('WINDOW', 6), ('CTE', 5),
                ('RECURSIVE', 8), ('TRIGGER', 6), ('PROCEDURE', 7)
            ]
            
            for feature, weight in advanced_features:
                count = combined_sql.count(feature)
                complexity += count * weight
            
            # Join complexity
            join_count = combined_sql.count('JOIN')
            complexity += join_count * 3
            
            return min(complexity, 100)  # Cap at 100
            
        except Exception as e:
            logger.warning(f"Error calculating complexity: {str(e)}")
            return 0
    
    def _generate_warnings(self, sql_content: str, dialect: str) -> List[str]:
        """Generate general warnings for the SQL content"""
        warnings = []
        
        try:
            upper_sql = sql_content.upper()
            
            # Check for deprecated features
            deprecated_patterns = {
                'mysql': [r'TYPE\s*=', r'ISAM', r'BDB'],
                'postgresql': [r'SERIAL\d*', r'MONEY'],
                'sqlserver': [r'TEXT\s', r'NTEXT\s', r'IMAGE\s']
            }
            
            if dialect in deprecated_patterns:
                for pattern in deprecated_patterns[dialect]:
                    if re.search(pattern, upper_sql):
                        warnings.append(f"Deprecated feature detected: {pattern}")
            
            # Check for performance issues
            if upper_sql.count('SELECT') > 10:
                warnings.append("High number of SELECT statements - consider query optimization")
            
            if len(sql_content) > 50000:  # Large SQL file
                warnings.append("Large SQL file detected - consider breaking into smaller chunks")
                
        except Exception as e:
            logger.warning(f"Error generating warnings: {str(e)}")
        
        return warnings
    
    def _generate_suggestions(self, operations: List[SQLOperation], tables: List[TableInfo], complexity: int) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []
        
        try:
            # Suggest based on complexity
            if complexity > 70:
                suggestions.append("High complexity detected - consider breaking into smaller operations")
                suggestions.append("Review query execution plan and add appropriate indexes")
            elif complexity > 40:
                suggestions.append("Medium complexity - monitor performance after migration")
            
            # Suggest based on operations
            if SQLOperation.CREATE in operations:
                suggestions.append("Consider adding appropriate indexes for new tables")
                suggestions.append("Review foreign key constraints for referential integrity")
            
            if len(tables) > 20:
                suggestions.append("Large number of tables - consider schema organization")
            
            # Default suggestion
            if not suggestions:
                suggestions.append("SQL appears well-structured for migration")
                
        except Exception as e:
            logger.warning(f"Error generating suggestions: {str(e)}")
        
        return suggestions
    
    def _estimate_execution_time(self, complexity: int, statement_count: int) -> str:
        """Estimate migration execution time"""
        try:
            # Base time calculation
            base_minutes = statement_count * 0.5  # 30 seconds per statement
            
            # Adjust for complexity
            complexity_multiplier = 1 + (complexity / 100)
            estimated_minutes = base_minutes * complexity_multiplier
            
            if estimated_minutes < 5:
                return "2-5 minutes"
            elif estimated_minutes < 15:
                return "5-15 minutes"
            elif estimated_minutes < 30:
                return "15-30 minutes"
            elif estimated_minutes < 60:
                return "30-60 minutes"
            else:
                return "1+ hours"
                
        except Exception as e:
            logger.warning(f"Error estimating execution time: {str(e)}")
            return "Unknown"


class SchemaExtractor:
    """Extract schema information from SQL DDL statements"""
    
    def __init__(self):
        self.parser = SQLParser()
    
    def extract_schema(self, ddl_sql: str, dialect: str = 'mysql') -> Dict[str, Any]:
        """Extract comprehensive schema information from DDL"""
        
        try:
            analysis = self.parser.analyze_sql(ddl_sql, dialect)
            
            schema_info = {
                'tables': {},
                'views': {},
                'indexes': {},
                'constraints': {},
                'procedures': {},
                'functions': {},
                'triggers': {},
                'sequences': {}
            }
            
            # Process each table
            for table in analysis.tables:
                schema_info['tables'][table.name] = {
                    'name': table.name,
                    'schema': table.schema,
                    'columns': [
                        {
                            'name': col.name,
                            'type': col.data_type,
                            'nullable': col.nullable,
                            'primary_key': col.primary_key,
                            'foreign_key': col.foreign_key,
                            'default': col.default_value
                        }
                        for col in table.columns
                    ],
                    'indexes': table.indexes,
                    'constraints': table.constraints
                }
            
            return schema_info
            
        except Exception as e:
            logger.error(f"Error extracting schema: {str(e)}")
            return {'error': str(e)}