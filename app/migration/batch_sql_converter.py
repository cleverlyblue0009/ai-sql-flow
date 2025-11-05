"""
Batch SQL Converter with Gemini-powered dialect detection and translation
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor
import json
import re

from .ai_translator import AITranslationEngine

logger = logging.getLogger(__name__)


class BatchSQLConverter:
    """Batch SQL conversion with dialect detection and parallel processing"""
    
    def __init__(self):
        self.translator = AITranslationEngine()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize Gemini for dialect detection
        from ..database.config import settings
        self.gemini_model = None
        self.use_gemini = False
        
        api_key = getattr(settings, 'gemini_api_key', None) or getattr(settings, 'google_api_key', None)
        if api_key and api_key.strip():
            try:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
                self.use_gemini = True
                logger.info("Gemini API initialized for dialect detection")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {str(e)}")
                self.use_gemini = False
    
    async def detect_sql_dialect(self, sql_content: str, filename: str) -> Dict[str, Any]:
        """
        Detect SQL dialect using Gemini API or rule-based fallback
        Returns: {
            "dialect": str,
            "confidence": float (0-100),
            "features": List[str],
            "reasoning": str
        }
        """
        try:
            if self.use_gemini and self.gemini_model:
                return await self._detect_with_gemini(sql_content, filename)
            else:
                return await self._detect_with_rules(sql_content, filename)
        except Exception as e:
            logger.error(f"Error detecting dialect for {filename}: {str(e)}")
            return {
                "dialect": "unknown",
                "confidence": 0,
                "features": [],
                "reasoning": f"Detection failed: {str(e)}"
            }
    
    async def _detect_with_gemini(self, sql_content: str, filename: str) -> Dict[str, Any]:
        """Use Gemini API for accurate dialect detection"""
        
        prompt = f"""Analyze this SQL code and identify its database dialect.

SQL Code:
```sql
{sql_content[:3000]}  # First 3000 chars for analysis
```

Identify:
1. The database dialect (mysql, postgresql, sqlserver, oracle, snowflake, sqlite, etc.)
2. Your confidence level (0-100)
3. Key dialect-specific features you detected
4. Brief reasoning

Respond in this EXACT JSON format:
{{
  "dialect": "dialect_name_lowercase",
  "confidence": 85,
  "features": ["feature1", "feature2", "feature3"],
  "reasoning": "Brief explanation of why you identified this dialect"
}}

IMPORTANT: Only output valid JSON, nothing else."""

        try:
            loop = asyncio.get_event_loop()
            
            def call_gemini():
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.1,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 1024,
                    }
                )
                return response.text
            
            response_text = await loop.run_in_executor(self.executor, call_gemini)
            
            # Parse JSON response
            # Remove markdown code blocks if present
            json_text = response_text.strip()
            if json_text.startswith("```"):
                lines = json_text.split("\n")
                json_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            result = json.loads(json_text)
            
            # Validate and normalize
            result["dialect"] = result.get("dialect", "unknown").lower()
            result["confidence"] = max(0, min(100, int(result.get("confidence", 50))))
            result["features"] = result.get("features", [])[:5]  # Limit to 5 features
            result["reasoning"] = result.get("reasoning", "Detected using AI analysis")[:200]
            
            logger.info(f"Gemini detected {result['dialect']} with {result['confidence']}% confidence for {filename}")
            return result
            
        except Exception as e:
            logger.error(f"Gemini detection failed: {str(e)}, falling back to rules")
            return await self._detect_with_rules(sql_content, filename)
    
    async def _detect_with_rules(self, sql_content: str, filename: str) -> Dict[str, Any]:
        """Fallback rule-based dialect detection"""
        
        upper_content = sql_content.upper()
        scores = {}
        features_found = {}
        
        # MySQL patterns
        mysql_patterns = [
            (r'AUTO_INCREMENT', 5),
            (r'ENGINE\s*=\s*(InnoDB|MyISAM)', 5),
            (r'CHARSET\s*=', 3),
            (r'`[^`]+`', 3),
            (r'LIMIT\s+\d+\s*,\s*\d+', 4),
            (r'DATE_FORMAT', 3),
            (r'IFNULL', 2),
            (r'TINYINT|MEDIUMINT|LONGTEXT', 3)
        ]
        
        # PostgreSQL patterns
        postgresql_patterns = [
            (r'SERIAL|BIGSERIAL', 5),
            (r'RETURNING', 4),
            (r'::', 3),
            (r'ARRAY\[', 4),
            (r'JSONB', 4),
            (r'UUID', 3),
            (r'GENERATE_ALWAYS\s+AS\s+IDENTITY', 5),
            (r'ILIKE', 3)
        ]
        
        # SQL Server patterns
        sqlserver_patterns = [
            (r'IDENTITY\s*\(\s*\d+\s*,\s*\d+\s*\)', 5),
            (r'\[dbo\]\.', 4),
            (r'NVARCHAR', 4),
            (r'GETDATE\(\)', 3),
            (r'TOP\s+\d+', 4),
            (r'\bGO\b', 5),
            (r'WITH\s+\(NOLOCK\)', 3)
        ]
        
        # Oracle patterns
        oracle_patterns = [
            (r'VARCHAR2', 5),
            (r'NUMBER\s*\(\s*\d+', 4),
            (r'SYSDATE', 4),
            (r'DUAL', 5),
            (r'ROWNUM', 4),
            (r'NVL\s*\(', 3),
            (r'CLOB|BLOB', 3)
        ]
        
        # Snowflake patterns
        snowflake_patterns = [
            (r'AUTOINCREMENT', 5),
            (r'VARIANT', 5),
            (r'FLATTEN\s*\(', 4),
            (r'CURRENT_TIMESTAMP\s*\(\)', 3),
            (r'DATEADD\s*\(', 3),
            (r'TRY_PARSE_JSON', 4),
            (r'QUALIFY', 5)
        ]
        
        dialects = {
            'mysql': mysql_patterns,
            'postgresql': postgresql_patterns,
            'sqlserver': sqlserver_patterns,
            'oracle': oracle_patterns,
            'snowflake': snowflake_patterns
        }
        
        # Score each dialect
        for dialect, patterns in dialects.items():
            score = 0
            features = []
            for pattern, weight in patterns:
                matches = len(re.findall(pattern, sql_content, re.IGNORECASE))
                if matches > 0:
                    score += matches * weight
                    features.append(pattern.replace('\\b', '').replace('\\s*', ' ')[:30])
            scores[dialect] = score
            features_found[dialect] = features[:5]
        
        # Find best match
        if max(scores.values()) == 0:
            return {
                "dialect": "unknown",
                "confidence": 0,
                "features": [],
                "reasoning": "No dialect-specific patterns detected"
            }
        
        best_dialect = max(scores.items(), key=lambda x: x[1])[0]
        total_score = sum(scores.values())
        confidence = min(95, int((scores[best_dialect] / total_score) * 100)) if total_score > 0 else 50
        
        return {
            "dialect": best_dialect,
            "confidence": confidence,
            "features": features_found[best_dialect],
            "reasoning": f"Rule-based detection using pattern matching"
        }
    
    async def convert_batch(
        self,
        files: List[Dict[str, Any]],
        target_dialect: str,
        conversion_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert batch of SQL files
        
        Args:
            files: List of {filename, content, source_dialect (optional)}
            target_dialect: Target database dialect
            conversion_options: Optional conversion settings
        
        Returns:
            {
                "files": [{
                    "filename": str,
                    "source_dialect": str,
                    "confidence": float,
                    "translated_sql": str,
                    "translation_confidence": float,
                    "warnings": [],
                    "errors": [],
                    "line_count_before": int,
                    "line_count_after": int,
                    "processing_time_ms": float
                }],
                "overall_confidence": float,
                "total_processing_time_ms": float,
                "success_count": int,
                "failure_count": int
            }
        """
        
        start_time = datetime.now()
        options = conversion_options or {}
        results = []
        
        # Process files in parallel
        tasks = []
        for file_data in files:
            task = self._convert_single_file(
                filename=file_data.get('filename', 'unknown.sql'),
                content=file_data.get('content', ''),
                source_dialect=file_data.get('source_dialect'),
                target_dialect=target_dialect,
                options=options
            )
            tasks.append(task)
        
        # Wait for all conversions to complete
        file_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        failure_count = 0
        total_confidence = 0
        
        for i, result in enumerate(file_results):
            if isinstance(result, Exception):
                logger.error(f"File {files[i].get('filename')} failed: {str(result)}")
                results.append({
                    "filename": files[i].get('filename', 'unknown.sql'),
                    "source_dialect": "unknown",
                    "confidence": 0,
                    "translated_sql": "",
                    "translation_confidence": 0,
                    "warnings": [],
                    "errors": [str(result)],
                    "line_count_before": 0,
                    "line_count_after": 0,
                    "processing_time_ms": 0
                })
                failure_count += 1
            else:
                results.append(result)
                if result.get('errors'):
                    failure_count += 1
                else:
                    success_count += 1
                    total_confidence += result.get('translation_confidence', 0)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        return {
            "files": results,
            "overall_confidence": total_confidence / max(1, success_count),
            "total_processing_time_ms": processing_time,
            "success_count": success_count,
            "failure_count": failure_count,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _convert_single_file(
        self,
        filename: str,
        content: str,
        source_dialect: Optional[str],
        target_dialect: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert a single SQL file"""
        
        file_start_time = datetime.now()
        
        try:
            # Detect source dialect if not provided
            if not source_dialect or source_dialect == "unknown":
                detection_result = await self.detect_sql_dialect(content, filename)
                source_dialect = detection_result["dialect"]
                detection_confidence = detection_result["confidence"]
                detected_features = detection_result["features"]
            else:
                detection_confidence = 100
                detected_features = []
            
            # Translate SQL
            translation_result = await self.translator.translate_sql_advanced(
                source_sql=content,
                source_dialect=source_dialect,
                target_dialect=target_dialect,
                optimization_level=options.get('optimization_level', 'standard')
            )
            
            # Format output with clean header
            translated_sql = self._format_output(
                translated_sql=translation_result.get('translated_sql', ''),
                filename=filename,
                source_dialect=source_dialect,
                target_dialect=target_dialect,
                confidence=detection_confidence,
                optimization_suggestions=translation_result.get('optimization_suggestions', [])
            )
            
            # Calculate line counts
            lines_before = len([l for l in content.split('\n') if l.strip()])
            lines_after = len([l for l in translated_sql.split('\n') if l.strip()])
            
            file_end_time = datetime.now()
            processing_time = (file_end_time - file_start_time).total_seconds() * 1000
            
            # Extract warnings and errors from validation
            validation = translation_result.get('validation_result', {})
            warnings = validation.get('warnings', [])
            errors = validation.get('errors', [])
            
            # Add detection warning if confidence is low
            if detection_confidence < 50:
                warnings.insert(0, f"Low detection confidence ({detection_confidence}%). Please review the conversion carefully.")
            
            return {
                "filename": filename,
                "source_dialect": source_dialect,
                "confidence": detection_confidence,
                "detected_features": detected_features,
                "translated_sql": translated_sql,
                "translation_confidence": translation_result.get('confidence_score', 0.8) * 100,
                "warnings": warnings,
                "errors": errors,
                "line_count_before": lines_before,
                "line_count_after": lines_after,
                "processing_time_ms": processing_time,
                "optimization_suggestions": translation_result.get('optimization_suggestions', [])
            }
            
        except Exception as e:
            logger.error(f"Error converting {filename}: {str(e)}")
            return {
                "filename": filename,
                "source_dialect": source_dialect or "unknown",
                "confidence": 0,
                "detected_features": [],
                "translated_sql": "",
                "translation_confidence": 0,
                "warnings": [],
                "errors": [f"Conversion failed: {str(e)}"],
                "line_count_before": 0,
                "line_count_after": 0,
                "processing_time_ms": 0,
                "optimization_suggestions": []
            }
    
    def _format_output(
        self,
        translated_sql: str,
        filename: str,
        source_dialect: str,
        target_dialect: str,
        confidence: float,
        optimization_suggestions: List[str]
    ) -> str:
        """Format translated SQL with professional header"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        header = f"""-- ============================================================
-- SQL Translation Report
-- ============================================================
-- Original File: {filename}
-- Source Database: {source_dialect.upper()}
-- Target Database: {target_dialect.upper()}
-- Detection Confidence: {confidence}%
-- Generated: {timestamp}
-- Translator: DataFlow AI SQL Converter
-- ============================================================

"""
        
        footer = ""
        if optimization_suggestions:
            footer = f"""

-- ============================================================
-- Optimization Suggestions
-- ============================================================
"""
            for i, suggestion in enumerate(optimization_suggestions[:5], 1):
                footer += f"-- {i}. {suggestion}\n"
            footer += "-- ============================================================\n"
        
        return header + translated_sql.strip() + footer
    
    def format_for_download(
        self,
        filename: str,
        translated_sql: str,
        file_type: str = 'sql'
    ) -> Dict[str, Any]:
        """Format file for download"""
        
        # Generate new filename
        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        new_filename = f"translated_{base_name}.{file_type}"
        
        return {
            "filename": new_filename,
            "content": translated_sql,
            "size": len(translated_sql),
            "mime_type": f"text/{file_type}",
            "encoding": "utf-8"
        }


# Global instance
batch_converter = BatchSQLConverter()
