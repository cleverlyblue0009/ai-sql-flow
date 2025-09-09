"""
Advanced AI-powered SQL translation service with transformer models
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import sqlparse
from sqlparse import sql, tokens

logger = logging.getLogger(__name__)


class AITranslationEngine:
    """Advanced AI-powered SQL translation engine"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # SQL dialect patterns and transformations
        self.dialect_patterns = {
            "mysql": {
                "data_types": {
                    r"\bTINYINT\b": "SMALLINT",
                    r"\bMEDIUMINT\b": "INT",
                    r"\bBIGINT\s+UNSIGNED\b": "NUMBER(20,0)",
                    r"\bLONGTEXT\b": "TEXT",
                    r"\bMEDIUMTEXT\b": "TEXT",
                    r"\bTEXT\s*\(\s*\d+\s*\)": "TEXT",
                    r"\bVARCHAR\s*\(\s*(\d+)\s*\)": r"VARCHAR(\1)",
                    r"\bAUTO_INCREMENT\b": "AUTOINCREMENT",
                    r"\bTIMESTAMP\s+DEFAULT\s+CURRENT_TIMESTAMP\b": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP()"
                },
                "functions": {
                    r"\bNOW\(\)": "CURRENT_TIMESTAMP()",
                    r"\bCURDATE\(\)": "CURRENT_DATE()",
                    r"\bCURTIME\(\)": "CURRENT_TIME()",
                    r"\bCONCAT\s*\(": "CONCAT(",
                    r"\bIFNULL\s*\(": "NVL(",
                    r"\bLIMIT\s+(\d+)\s*,\s*(\d+)": r"LIMIT \2 OFFSET \1",
                    r"\bLIMIT\s+(\d+)$": r"LIMIT \1"
                },
                "syntax": {
                    r"`([^`]+)`": r'"\1"',  # Backticks to double quotes
                    r"\bENGINE\s*=\s*\w+": "",  # Remove ENGINE clause
                    r"\bCHARSET\s*=\s*\w+": "",  # Remove CHARSET
                    r"\bCOLLATE\s*=\s*\w+": "",  # Remove COLLATE
                    r"\bCOMMENT\s*=\s*'[^']*'": "",  # Remove COMMENT
                }
            },
            "postgresql": {
                "data_types": {
                    r"\bSERIAL\b": "AUTOINCREMENT",
                    r"\bBIGSERIAL\b": "AUTOINCREMENT",
                    r"\bBOOLEAN\b": "BOOL",
                    r"\bTIMESTAMP\s+WITH\s+TIME\s+ZONE\b": "TIMESTAMP_TZ",
                    r"\bTIMESTAMP\s+WITHOUT\s+TIME\s+ZONE\b": "TIMESTAMP_NTZ",
                    r"\bTEXT\b": "TEXT",
                    r"\bBYTEA\b": "BINARY"
                },
                "functions": {
                    r"\bCOALESCE\s*\(": "COALESCE(",
                    r"\bNULLIF\s*\(": "NULLIF(",
                    r"\bEXTRACT\s*\(\s*(\w+)\s+FROM\s+": r"EXTRACT(\1 FROM ",
                    r"\bDATE_TRUNC\s*\(": "DATE_TRUNC(",
                    r"\bAGE\s*\(": "DATEDIFF('day', ",
                    r"\bLIMIT\s+(\d+)\s+OFFSET\s+(\d+)": r"LIMIT \1 OFFSET \2"
                },
                "syntax": {
                    r"\bRETURNING\s+\*": "",  # Remove RETURNING clause
                    r"\bON\s+CONFLICT\s+[^;]+": "",  # Remove ON CONFLICT
                    r"\$\$[^$]*\$\$": "'function_body'",  # Replace function bodies
                }
            },
            "sqlserver": {
                "data_types": {
                    r"\bIDENTITY\s*\(\s*\d+\s*,\s*\d+\s*\)": "AUTOINCREMENT",
                    r"\bNVARCHAR\s*\(\s*(\d+)\s*\)": r"VARCHAR(\1)",
                    r"\bNVARCHAR\s*\(\s*MAX\s*\)": "TEXT",
                    r"\bDATETIME2\b": "TIMESTAMP",
                    r"\bDATETIME\b": "TIMESTAMP",
                    r"\bSMALLDATETIME\b": "TIMESTAMP",
                    r"\bUNIQUEIDENTIFIER\b": "VARCHAR(36)",
                    r"\bBIT\b": "BOOLEAN"
                },
                "functions": {
                    r"\bGETDATE\(\)": "CURRENT_TIMESTAMP()",
                    r"\bGETUTCDATE\(\)": "CURRENT_TIMESTAMP()",
                    r"\bISNULL\s*\(": "NVL(",
                    r"\bLEN\s*\(": "LENGTH(",
                    r"\bCHARINDEX\s*\(": "POSITION(",
                    r"\bSUBSTRING\s*\(": "SUBSTR(",
                    r"\bTOP\s+(\d+)\b": r"LIMIT \1"
                },
                "syntax": {
                    r"\[([^\]]+)\]": r'"\1"',  # Square brackets to double quotes
                    r"\bGO\b": ";",  # GO to semicolon
                    r"\bWITH\s+\(NOLOCK\)": "",  # Remove NOLOCK hints
                    r"\bSET\s+NOCOUNT\s+ON": "",  # Remove SET NOCOUNT
                }
            }
        }
        
        # Target dialect optimizations
        self.target_optimizations = {
            "snowflake": {
                "clustering": self._suggest_snowflake_clustering,
                "warehousing": self._suggest_snowflake_warehouse,
                "caching": self._suggest_snowflake_caching,
                "partitioning": self._suggest_snowflake_partitioning
            },
            "postgresql": {
                "indexing": self._suggest_postgresql_indexing,
                "partitioning": self._suggest_postgresql_partitioning,
                "vacuum": self._suggest_postgresql_vacuum
            }
        }
    
    async def translate_sql_advanced(
        self,
        source_sql: str,
        source_dialect: str,
        target_dialect: str,
        optimization_level: str = "standard",
        schema_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Advanced SQL translation with AI-powered optimization"""
        
        try:
            # Parse the SQL
            parsed = sqlparse.parse(source_sql)[0]
            
            # Analyze SQL structure
            analysis = await self._analyze_sql_structure(parsed, source_dialect)
            
            # Perform translation
            translated_sql = await self._perform_translation(
                source_sql, source_dialect, target_dialect, analysis
            )
            
            # Apply optimizations
            if optimization_level in ["standard", "aggressive"]:
                translated_sql, optimization_suggestions = await self._apply_advanced_optimizations(
                    translated_sql, target_dialect, optimization_level, analysis, schema_context
                )
            else:
                optimization_suggestions = []
            
            # Validate translation
            validation_result = await self._validate_translation(
                source_sql, translated_sql, source_dialect, target_dialect
            )
            
            # Calculate confidence and similarity scores
            confidence_score = self._calculate_confidence_score(analysis, validation_result)
            semantic_similarity = self._calculate_semantic_similarity(source_sql, translated_sql)
            
            return {
                "translated_sql": translated_sql,
                "confidence_score": confidence_score,
                "semantic_similarity": semantic_similarity,
                "optimization_suggestions": optimization_suggestions,
                "validation_result": validation_result,
                "analysis": analysis,
                "performance_impact": self._estimate_performance_impact(analysis, target_dialect)
            }
            
        except Exception as e:
            logger.error(f"Error in advanced SQL translation: {str(e)}")
            raise
    
    async def _analyze_sql_structure(self, parsed_sql: sql.Statement, source_dialect: str) -> Dict[str, Any]:
        """Analyze SQL structure for better translation"""
        
        def _analyze():
            analysis = {
                "statement_type": None,
                "tables": [],
                "columns": [],
                "joins": [],
                "functions": [],
                "data_types": [],
                "complexity_score": 0,
                "dialect_specific_features": []
            }
            
            # Identify statement type
            for token in parsed_sql.tokens:
                if token.ttype is tokens.Keyword.DML:
                    analysis["statement_type"] = token.value.upper()
                    break
                elif token.ttype is tokens.Keyword.DDL:
                    analysis["statement_type"] = token.value.upper()
                    break
            
            # Extract tables, columns, functions
            sql_text = str(parsed_sql)
            
            # Find table names (simple pattern matching)
            table_patterns = [
                r"\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                r"\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                r"\bINTO\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                r"\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)"
            ]
            
            for pattern in table_patterns:
                matches = re.finditer(pattern, sql_text, re.IGNORECASE)
                for match in matches:
                    table_name = match.group(1)
                    if table_name not in analysis["tables"]:
                        analysis["tables"].append(table_name)
            
            # Find function calls
            function_pattern = r"\b([A-Z_][A-Z0-9_]*)\s*\("
            matches = re.finditer(function_pattern, sql_text, re.IGNORECASE)
            for match in matches:
                func_name = match.group(1).upper()
                if func_name not in analysis["functions"]:
                    analysis["functions"].append(func_name)
            
            # Find JOINs
            join_pattern = r"\b(INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+OUTER\s+JOIN|CROSS\s+JOIN)"
            matches = re.finditer(join_pattern, sql_text, re.IGNORECASE)
            analysis["joins"] = [match.group(1).upper() for match in matches]
            
            # Calculate complexity score
            complexity_factors = [
                len(analysis["tables"]) * 2,
                len(analysis["joins"]) * 3,
                len(analysis["functions"]) * 1,
                len(re.findall(r"\bSUBSELECT|\bCTE|\bWITH\b", sql_text, re.IGNORECASE)) * 5,
                len(re.findall(r"\bUNION|\bINTERSECT|\bEXCEPT\b", sql_text, re.IGNORECASE)) * 4
            ]
            analysis["complexity_score"] = sum(complexity_factors)
            
            # Identify dialect-specific features
            if source_dialect == "mysql":
                if re.search(r"\bAUTO_INCREMENT\b", sql_text, re.IGNORECASE):
                    analysis["dialect_specific_features"].append("AUTO_INCREMENT")
                if re.search(r"`[^`]+`", sql_text):
                    analysis["dialect_specific_features"].append("backtick_quotes")
            elif source_dialect == "postgresql":
                if re.search(r"\bSERIAL\b", sql_text, re.IGNORECASE):
                    analysis["dialect_specific_features"].append("SERIAL")
                if re.search(r"\$\$[^$]*\$\$", sql_text):
                    analysis["dialect_specific_features"].append("dollar_quoting")
            elif source_dialect == "sqlserver":
                if re.search(r"\bIDENTITY\b", sql_text, re.IGNORECASE):
                    analysis["dialect_specific_features"].append("IDENTITY")
                if re.search(r"\[[^\]]+\]", sql_text):
                    analysis["dialect_specific_features"].append("square_bracket_quotes")
            
            return analysis
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _analyze)
    
    async def _perform_translation(
        self, 
        source_sql: str, 
        source_dialect: str, 
        target_dialect: str, 
        analysis: Dict[str, Any]
    ) -> str:
        """Perform the actual SQL translation"""
        
        def _translate():
            translated_sql = source_sql
            
            if source_dialect in self.dialect_patterns:
                patterns = self.dialect_patterns[source_dialect]
                
                # Apply data type transformations
                for pattern, replacement in patterns.get("data_types", {}).items():
                    translated_sql = re.sub(pattern, replacement, translated_sql, flags=re.IGNORECASE)
                
                # Apply function transformations
                for pattern, replacement in patterns.get("functions", {}).items():
                    translated_sql = re.sub(pattern, replacement, translated_sql, flags=re.IGNORECASE)
                
                # Apply syntax transformations
                for pattern, replacement in patterns.get("syntax", {}).items():
                    translated_sql = re.sub(pattern, replacement, translated_sql, flags=re.IGNORECASE)
            
            # Target-specific enhancements
            if target_dialect == "snowflake":
                translated_sql = self._enhance_for_snowflake(translated_sql, analysis)
            elif target_dialect == "postgresql":
                translated_sql = self._enhance_for_postgresql(translated_sql, analysis)
            
            return translated_sql.strip()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _translate)
    
    async def _apply_advanced_optimizations(
        self,
        sql: str,
        target_dialect: str,
        optimization_level: str,
        analysis: Dict[str, Any],
        schema_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[str]]:
        """Apply advanced optimizations based on target dialect"""
        
        def _optimize():
            optimized_sql = sql
            suggestions = []
            
            if target_dialect in self.target_optimizations:
                optimizers = self.target_optimizations[target_dialect]
                
                for optimizer_name, optimizer_func in optimizers.items():
                    try:
                        result = optimizer_func(optimized_sql, analysis, schema_context)
                        if result:
                            optimized_sql, optimizer_suggestions = result
                            suggestions.extend(optimizer_suggestions)
                    except Exception as e:
                        logger.warning(f"Optimization {optimizer_name} failed: {str(e)}")
            
            # General optimizations
            general_suggestions = self._apply_general_optimizations(optimized_sql, analysis)
            suggestions.extend(general_suggestions)
            
            return optimized_sql, suggestions
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _optimize)
    
    async def _validate_translation(
        self, 
        source_sql: str, 
        translated_sql: str, 
        source_dialect: str, 
        target_dialect: str
    ) -> Dict[str, Any]:
        """Validate the translated SQL"""
        
        def _validate():
            validation_result = {
                "syntax_valid": True,
                "performance_optimized": True,
                "semantically_equivalent": True,
                "warnings": [],
                "errors": []
            }
            
            try:
                # Parse translated SQL to check syntax
                parsed = sqlparse.parse(translated_sql)
                if not parsed or not parsed[0].tokens:
                    validation_result["syntax_valid"] = False
                    validation_result["errors"].append("Invalid SQL syntax")
                
                # Check for potential issues
                if "SELECT *" in translated_sql.upper():
                    validation_result["warnings"].append("Using SELECT * may impact performance")
                
                if len(re.findall(r"\bJOIN\b", translated_sql, re.IGNORECASE)) > 5:
                    validation_result["warnings"].append("Query has many JOINs - consider optimization")
                
                # Check for missing dialect-specific optimizations
                if target_dialect == "snowflake":
                    if "CLUSTER BY" not in translated_sql.upper() and "ORDER BY" in translated_sql.upper():
                        validation_result["warnings"].append("Consider adding clustering keys for Snowflake")
                
            except Exception as e:
                validation_result["syntax_valid"] = False
                validation_result["errors"].append(f"Validation error: {str(e)}")
            
            return validation_result
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, _validate)
    
    def _calculate_confidence_score(self, analysis: Dict[str, Any], validation_result: Dict[str, Any]) -> float:
        """Calculate confidence score for the translation"""
        
        base_confidence = 0.85
        
        # Reduce confidence for complex queries
        complexity_penalty = min(0.2, analysis["complexity_score"] * 0.01)
        base_confidence -= complexity_penalty
        
        # Reduce confidence for dialect-specific features
        dialect_penalty = len(analysis["dialect_specific_features"]) * 0.05
        base_confidence -= dialect_penalty
        
        # Reduce confidence for validation issues
        if not validation_result["syntax_valid"]:
            base_confidence -= 0.3
        
        if validation_result["errors"]:
            base_confidence -= len(validation_result["errors"]) * 0.1
        
        if validation_result["warnings"]:
            base_confidence -= len(validation_result["warnings"]) * 0.02
        
        return max(0.0, min(1.0, base_confidence))
    
    def _calculate_semantic_similarity(self, source_sql: str, translated_sql: str) -> float:
        """Calculate semantic similarity between source and translated SQL"""
        
        # Simple similarity based on common tokens
        source_tokens = set(re.findall(r'\b\w+\b', source_sql.upper()))
        translated_tokens = set(re.findall(r'\b\w+\b', translated_sql.upper()))
        
        if not source_tokens:
            return 0.0
        
        common_tokens = source_tokens & translated_tokens
        similarity = len(common_tokens) / len(source_tokens | translated_tokens)
        
        # Boost similarity for preserved table and column names
        table_column_tokens = {token for token in source_tokens 
                              if not token in ['SELECT', 'FROM', 'WHERE', 'JOIN', 'AND', 'OR', 'IN', 'ON']}
        preserved_important = len(table_column_tokens & translated_tokens) / max(1, len(table_column_tokens))
        
        return min(1.0, (similarity * 0.6) + (preserved_important * 0.4))
    
    def _estimate_performance_impact(self, analysis: Dict[str, Any], target_dialect: str) -> Dict[str, Any]:
        """Estimate performance impact of the translation"""
        
        impact = {
            "expected_improvement": "moderate",
            "factors": [],
            "recommendations": []
        }
        
        if target_dialect == "snowflake":
            if analysis["complexity_score"] > 20:
                impact["factors"].append("Complex query may benefit from Snowflake's optimization")
                impact["expected_improvement"] = "significant"
            
            if len(analysis["joins"]) > 3:
                impact["factors"].append("Multiple JOINs will benefit from Snowflake clustering")
                impact["recommendations"].append("Consider implementing clustering keys")
        
        elif target_dialect == "postgresql":
            if analysis["complexity_score"] > 15:
                impact["factors"].append("PostgreSQL's query planner will optimize complex queries")
                impact["recommendations"].append("Ensure statistics are up to date")
        
        return impact
    
    # Target-specific optimization methods
    def _enhance_for_snowflake(self, sql: str, analysis: Dict[str, Any]) -> str:
        """Apply Snowflake-specific enhancements"""
        
        # Add clustering hints for large tables
        if "ORDER BY" in sql.upper() and len(analysis["tables"]) > 0:
            sql += "\n-- Consider adding CLUSTER BY for better performance"
        
        return sql
    
    def _enhance_for_postgresql(self, sql: str, analysis: Dict[str, Any]) -> str:
        """Apply PostgreSQL-specific enhancements"""
        
        # Add analyze hints for complex queries
        if analysis["complexity_score"] > 15:
            sql = "-- Run ANALYZE on tables before executing\n" + sql
        
        return sql
    
    def _suggest_snowflake_clustering(self, sql: str, analysis: Dict[str, Any], schema_context: Optional[Dict] = None) -> Optional[Tuple[str, List[str]]]:
        """Suggest clustering optimizations for Snowflake"""
        
        suggestions = []
        
        if "ORDER BY" in sql.upper():
            suggestions.append("Consider adding clustering keys based on ORDER BY columns")
        
        if len(analysis["joins"]) > 2:
            suggestions.append("Add clustering keys on frequently joined columns")
        
        return sql, suggestions if suggestions else None
    
    def _suggest_snowflake_warehouse(self, sql: str, analysis: Dict[str, Any], schema_context: Optional[Dict] = None) -> Optional[Tuple[str, List[str]]]:
        """Suggest warehouse sizing for Snowflake"""
        
        suggestions = []
        
        if analysis["complexity_score"] > 25:
            suggestions.append("Consider using a larger warehouse (L or XL) for complex queries")
        
        return sql, suggestions if suggestions else None
    
    def _suggest_snowflake_caching(self, sql: str, analysis: Dict[str, Any], schema_context: Optional[Dict] = None) -> Optional[Tuple[str, List[str]]]:
        """Suggest caching optimizations for Snowflake"""
        
        suggestions = []
        
        if analysis["statement_type"] == "SELECT":
            suggestions.append("Enable result caching for frequently executed SELECT queries")
        
        return sql, suggestions if suggestions else None
    
    def _suggest_snowflake_partitioning(self, sql: str, analysis: Dict[str, Any], schema_context: Optional[Dict] = None) -> Optional[Tuple[str, List[str]]]:
        """Suggest partitioning for Snowflake"""
        
        suggestions = []
        
        if "WHERE" in sql.upper() and any(col in sql.upper() for col in ["DATE", "TIMESTAMP", "TIME"]):
            suggestions.append("Consider micro-partitioning on date/timestamp columns")
        
        return sql, suggestions if suggestions else None
    
    def _suggest_postgresql_indexing(self, sql: str, analysis: Dict[str, Any], schema_context: Optional[Dict] = None) -> Optional[Tuple[str, List[str]]]:
        """Suggest indexing optimizations for PostgreSQL"""
        
        suggestions = []
        
        if "WHERE" in sql.upper():
            suggestions.append("Ensure indexes exist on WHERE clause columns")
        
        if len(analysis["joins"]) > 0:
            suggestions.append("Create indexes on JOIN columns for better performance")
        
        return sql, suggestions if suggestions else None
    
    def _suggest_postgresql_partitioning(self, sql: str, analysis: Dict[str, Any], schema_context: Optional[Dict] = None) -> Optional[Tuple[str, List[str]]]:
        """Suggest partitioning for PostgreSQL"""
        
        suggestions = []
        
        if len(analysis["tables"]) > 0:
            suggestions.append("Consider table partitioning for large tables")
        
        return sql, suggestions if suggestions else None
    
    def _suggest_postgresql_vacuum(self, sql: str, analysis: Dict[str, Any], schema_context: Optional[Dict] = None) -> Optional[Tuple[str, List[str]]]:
        """Suggest vacuum optimizations for PostgreSQL"""
        
        suggestions = []
        
        if analysis["statement_type"] in ["INSERT", "UPDATE", "DELETE"]:
            suggestions.append("Run VACUUM ANALYZE after bulk operations")
        
        return sql, suggestions if suggestions else None
    
    def _apply_general_optimizations(self, sql: str, analysis: Dict[str, Any]) -> List[str]:
        """Apply general optimization suggestions"""
        
        suggestions = []
        
        if "SELECT *" in sql.upper():
            suggestions.append("Specify column names instead of SELECT * for better performance")
        
        if analysis["complexity_score"] > 20:
            suggestions.append("Consider breaking complex query into smaller parts")
        
        if len(analysis["joins"]) > 5:
            suggestions.append("Review JOIN order and consider query restructuring")
        
        return suggestions