import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
# ML imports with fallback for development
try:
    from sklearn.impute import SimpleImputer, KNNImputer, IterativeImputer
    from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
    from sklearn.ensemble import IsolationForest
    from sklearn.cluster import DBSCAN
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    # Fallback classes for development without sklearn
    class MockMLClass:
        def __init__(self, *args, **kwargs):
            pass
        def fit(self, *args, **kwargs):
            return self
        def predict(self, *args, **kwargs):
            return []
        def fit_predict(self, *args, **kwargs):
            return []
        def fit_transform(self, *args, **kwargs):
            return []
        def transform(self, *args, **kwargs):
            return []
    
    SimpleImputer = MockMLClass
    KNNImputer = MockMLClass
    IterativeImputer = MockMLClass
    StandardScaler = MockMLClass
    RobustScaler = MockMLClass
    MinMaxScaler = MockMLClass
    IsolationForest = MockMLClass
    DBSCAN = MockMLClass
    TfidfVectorizer = MockMLClass
    cosine_similarity = lambda x, y=None: [[1.0]]
    SKLEARN_AVAILABLE = False
import re
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .schemas import DataCleaningResult

logger = logging.getLogger(__name__)


class DataCleaner:
    """AI-powered data cleaning engine"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.cleaning_operations = {
            "remove_duplicates": self._remove_duplicates,
            "fill_missing": self._fill_missing_values,
            "remove_outliers": self._remove_outliers,
            "standardize_format": self._standardize_format,
            "correct_types": self._correct_data_types,
            "normalize_values": self._normalize_values,
            "smart_duplicate_detection": self._smart_duplicate_detection,
            "ml_imputation": self._ml_imputation,
            "anomaly_detection": self._anomaly_detection,
            "text_standardization": self._text_standardization,
            "auto_encoding_detection": self._auto_encoding_detection
        }
    
    async def clean_data(
        self,
        df: pd.DataFrame,
        cleaning_operations: List[Dict[str, Any]],
        preview_only: bool = False
    ) -> DataCleaningResult:
        """Execute data cleaning operations"""
        
        try:
            original_df = df.copy()
            cleaned_df = df.copy()
            modifications = {}
            cleaning_summary = {}
            
            logger.info(f"Starting data cleaning with {len(cleaning_operations)} operations")
            
            # Execute cleaning operations in order
            for operation in cleaning_operations:
                op_name = operation["operation"]
                op_params = operation.get("parameters", {})
                
                if op_name in self.cleaning_operations:
                    logger.info(f"Executing operation: {op_name}")
                    
                    # Execute operation (handle both sync and async)
                    operation_func = self.cleaning_operations[op_name]
                    if asyncio.iscoroutinefunction(operation_func):
                        result = await operation_func(cleaned_df, op_params)
                    else:
                        result = operation_func(cleaned_df, op_params)
                    
                    cleaned_df = result["data"]
                    modifications[op_name] = result["modifications"]
                    cleaning_summary[op_name] = result["summary"]
                else:
                    logger.warning(f"Unknown cleaning operation: {op_name}")
            
            # Calculate quality improvements
            quality_improvement = self._calculate_quality_improvement(original_df, cleaned_df)
            
            # Generate preview data if requested
            preview_data = None
            if preview_only and len(cleaned_df) > 0:
                preview_data = cleaned_df.head(100).to_dict('records')
            
            return DataCleaningResult(
                original_rows=len(original_df),
                cleaned_rows=len(cleaned_df),
                removed_rows=len(original_df) - len(cleaned_df),
                modifications=modifications,
                cleaning_summary=cleaning_summary,
                quality_improvement=quality_improvement,
                preview_data=preview_data
            )
            
        except Exception as e:
            logger.error(f"Error in data cleaning: {str(e)}")
            raise
    
    def _remove_duplicates(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove duplicate records"""
        
        try:
            subset_columns = params.get("columns", None)
            keep_method = params.get("keep", "first")  # first, last, False
            
            original_count = len(df)
            
            # Remove duplicates
            cleaned_df = df.drop_duplicates(subset=subset_columns, keep=keep_method)
            
            duplicates_removed = original_count - len(cleaned_df)
            
            return {
                "data": cleaned_df,
                "modifications": duplicates_removed,
                "summary": {
                    "duplicates_removed": duplicates_removed,
                    "duplicate_percentage": round((duplicates_removed / original_count) * 100, 2),
                    "columns_used": subset_columns or "all"
                }
            }
            
        except Exception as e:
            logger.error(f"Error removing duplicates: {str(e)}")
            return {"data": df, "modifications": 0, "summary": {"error": str(e)}}
    
    def _fill_missing_values(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fill missing values using various strategies"""
        
        try:
            strategy = params.get("strategy", "auto")  # auto, mean, median, mode, constant, knn
            columns = params.get("columns", df.columns.tolist())
            constant_value = params.get("constant_value", None)
            
            cleaned_df = df.copy()
            modifications = {}
            
            for col in columns:
                if col not in df.columns:
                    continue
                
                original_missing = df[col].isnull().sum()
                if original_missing == 0:
                    continue
                
                # Determine strategy for column
                if strategy == "auto":
                    if pd.api.types.is_numeric_dtype(df[col]):
                        # Use median for numeric data
                        fill_strategy = "median"
                    else:
                        # Use mode for categorical data
                        fill_strategy = "mode"
                else:
                    fill_strategy = strategy
                
                # Apply filling strategy
                if fill_strategy == "mean" and pd.api.types.is_numeric_dtype(df[col]):
                    cleaned_df[col].fillna(df[col].mean(), inplace=True)
                elif fill_strategy == "median" and pd.api.types.is_numeric_dtype(df[col]):
                    cleaned_df[col].fillna(df[col].median(), inplace=True)
                elif fill_strategy == "mode":
                    mode_value = df[col].mode()
                    if not mode_value.empty:
                        cleaned_df[col].fillna(mode_value.iloc[0], inplace=True)
                elif fill_strategy == "constant":
                    cleaned_df[col].fillna(constant_value, inplace=True)
                elif fill_strategy == "knn" and pd.api.types.is_numeric_dtype(df[col]):
                    # Use KNN imputation for numeric columns
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 1:
                        imputer = KNNImputer(n_neighbors=5)
                        numeric_data = imputer.fit_transform(df[numeric_cols])
                        col_idx = list(numeric_cols).index(col)
                        cleaned_df[col] = numeric_data[:, col_idx]
                
                filled_count = original_missing - cleaned_df[col].isnull().sum()
                modifications[col] = int(filled_count)
            
            total_filled = sum(modifications.values())
            
            return {
                "data": cleaned_df,
                "modifications": total_filled,
                "summary": {
                    "total_filled": total_filled,
                    "columns_processed": len([col for col in columns if col in modifications]),
                    "strategy_used": strategy,
                    "by_column": modifications
                }
            }
            
        except Exception as e:
            logger.error(f"Error filling missing values: {str(e)}")
            return {"data": df, "modifications": 0, "summary": {"error": str(e)}}
    
    def _remove_outliers(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove outlier values"""
        
        try:
            method = params.get("method", "iqr")  # iqr, zscore, isolation_forest
            columns = params.get("columns", df.select_dtypes(include=[np.number]).columns.tolist())
            threshold = params.get("threshold", 1.5)  # For IQR method
            
            cleaned_df = df.copy()
            outliers_removed = 0
            outliers_by_column = {}
            
            for col in columns:
                if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                    continue
                
                series = df[col].dropna()
                if len(series) < 10:  # Skip if too few values
                    continue
                
                outlier_mask = pd.Series([False] * len(df), index=df.index)
                
                if method == "iqr":
                    Q1 = series.quantile(0.25)
                    Q3 = series.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - threshold * IQR
                    upper_bound = Q3 + threshold * IQR
                    
                    outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
                
                elif method == "zscore":
                    z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                    outlier_mask = z_scores > threshold
                
                column_outliers = outlier_mask.sum()
                if column_outliers > 0:
                    outliers_by_column[col] = int(column_outliers)
                    outliers_removed += column_outliers
            
            # Remove rows with outliers
            if outliers_removed > 0:
                all_outlier_mask = pd.Series([False] * len(df), index=df.index)
                for col in outliers_by_column.keys():
                    if method == "iqr":
                        Q1 = df[col].quantile(0.25)
                        Q3 = df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound = Q1 - threshold * IQR
                        upper_bound = Q3 + threshold * IQR
                        all_outlier_mask |= (df[col] < lower_bound) | (df[col] > upper_bound)
                
                cleaned_df = df[~all_outlier_mask]
            
            return {
                "data": cleaned_df,
                "modifications": outliers_removed,
                "summary": {
                    "outliers_removed": outliers_removed,
                    "method_used": method,
                    "columns_processed": len(outliers_by_column),
                    "by_column": outliers_by_column
                }
            }
            
        except Exception as e:
            logger.error(f"Error removing outliers: {str(e)}")
            return {"data": df, "modifications": 0, "summary": {"error": str(e)}}
    
    def _standardize_format(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize data formats"""
        
        try:
            columns = params.get("columns", [])
            format_rules = params.get("format_rules", {})
            
            cleaned_df = df.copy()
            modifications = {}
            
            for col in columns:
                if col not in df.columns:
                    continue
                
                original_values = cleaned_df[col].copy()
                changes_made = 0
                
                # Apply format rules
                if col in format_rules:
                    rule = format_rules[col]
                    
                    if rule.get("case") == "lower":
                        cleaned_df[col] = cleaned_df[col].astype(str).str.lower()
                    elif rule.get("case") == "upper":
                        cleaned_df[col] = cleaned_df[col].astype(str).str.upper()
                    elif rule.get("case") == "title":
                        cleaned_df[col] = cleaned_df[col].astype(str).str.title()
                    
                    # Remove extra whitespace
                    if rule.get("trim", True):
                        cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
                    
                    # Apply regex patterns
                    if "regex_replace" in rule:
                        pattern = rule["regex_replace"]["pattern"]
                        replacement = rule["regex_replace"]["replacement"]
                        cleaned_df[col] = cleaned_df[col].astype(str).str.replace(pattern, replacement, regex=True)
                    
                    # Count changes
                    changes_made = (original_values != cleaned_df[col]).sum()
                
                modifications[col] = int(changes_made)
            
            total_changes = sum(modifications.values())
            
            return {
                "data": cleaned_df,
                "modifications": total_changes,
                "summary": {
                    "total_changes": total_changes,
                    "columns_processed": len(columns),
                    "by_column": modifications
                }
            }
            
        except Exception as e:
            logger.error(f"Error standardizing format: {str(e)}")
            return {"data": df, "modifications": 0, "summary": {"error": str(e)}}
    
    def _correct_data_types(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Correct data types based on content analysis"""
        
        try:
            type_corrections = params.get("type_corrections", {})
            auto_detect = params.get("auto_detect", True)
            
            cleaned_df = df.copy()
            corrections_made = {}
            
            # Auto-detect types if enabled
            if auto_detect:
                for col in df.columns:
                    if col not in type_corrections:
                        inferred_type = self._infer_best_type(df[col])
                        if inferred_type != str(df[col].dtype):
                            type_corrections[col] = inferred_type
            
            # Apply type corrections
            for col, target_type in type_corrections.items():
                if col not in df.columns:
                    continue
                
                try:
                    original_type = str(df[col].dtype)
                    
                    if target_type == "numeric":
                        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
                    elif target_type == "datetime":
                        cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
                    elif target_type == "boolean":
                        cleaned_df[col] = cleaned_df[col].astype(str).str.lower().map({
                            'true': True, 'false': False, '1': True, '0': False,
                            'yes': True, 'no': False, 't': True, 'f': False,
                            'y': True, 'n': False
                        })
                    elif target_type == "category":
                        cleaned_df[col] = cleaned_df[col].astype('category')
                    
                    new_type = str(cleaned_df[col].dtype)
                    if original_type != new_type:
                        corrections_made[col] = {"from": original_type, "to": new_type}
                
                except Exception as e:
                    logger.warning(f"Failed to convert {col} to {target_type}: {str(e)}")
            
            return {
                "data": cleaned_df,
                "modifications": len(corrections_made),
                "summary": {
                    "types_corrected": len(corrections_made),
                    "corrections": corrections_made
                }
            }
            
        except Exception as e:
            logger.error(f"Error correcting data types: {str(e)}")
            return {"data": df, "modifications": 0, "summary": {"error": str(e)}}
    
    def _normalize_values(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize numeric values"""
        
        try:
            columns = params.get("columns", df.select_dtypes(include=[np.number]).columns.tolist())
            method = params.get("method", "standard")  # standard, minmax, robust
            
            cleaned_df = df.copy()
            normalized_columns = []
            
            numeric_data = cleaned_df[columns].select_dtypes(include=[np.number])
            
            if len(numeric_data.columns) > 0:
                if method == "standard":
                    scaler = StandardScaler()
                    scaled_data = scaler.fit_transform(numeric_data)
                    cleaned_df[numeric_data.columns] = scaled_data
                elif method == "minmax":
                    from sklearn.preprocessing import MinMaxScaler
                    scaler = MinMaxScaler()
                    scaled_data = scaler.fit_transform(numeric_data)
                    cleaned_df[numeric_data.columns] = scaled_data
                elif method == "robust":
                    from sklearn.preprocessing import RobustScaler
                    scaler = RobustScaler()
                    scaled_data = scaler.fit_transform(numeric_data)
                    cleaned_df[numeric_data.columns] = scaled_data
                
                normalized_columns = list(numeric_data.columns)
            
            return {
                "data": cleaned_df,
                "modifications": len(normalized_columns),
                "summary": {
                    "columns_normalized": len(normalized_columns),
                    "method_used": method,
                    "columns": normalized_columns
                }
            }
            
        except Exception as e:
            logger.error(f"Error normalizing values: {str(e)}")
            return {"data": df, "modifications": 0, "summary": {"error": str(e)}}
    
    def _calculate_quality_improvement(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> Dict[str, float]:
        """Calculate quality improvement metrics"""
        
        try:
            improvements = {}
            
            # Completeness improvement
            original_completeness = ((original_df.count().sum()) / original_df.size) * 100
            cleaned_completeness = ((cleaned_df.count().sum()) / cleaned_df.size) * 100 if cleaned_df.size > 0 else 0
            improvements["completeness"] = round(cleaned_completeness - original_completeness, 2)
            
            # Uniqueness improvement (duplicate reduction)
            original_duplicates = len(original_df) - len(original_df.drop_duplicates())
            cleaned_duplicates = len(cleaned_df) - len(cleaned_df.drop_duplicates()) if len(cleaned_df) > 0 else 0
            
            original_uniqueness = ((len(original_df) - original_duplicates) / len(original_df)) * 100
            cleaned_uniqueness = ((len(cleaned_df) - cleaned_duplicates) / len(cleaned_df)) * 100 if len(cleaned_df) > 0 else 100
            improvements["uniqueness"] = round(cleaned_uniqueness - original_uniqueness, 2)
            
            # Overall quality improvement (estimated)
            improvements["overall"] = round((improvements["completeness"] + improvements["uniqueness"]) / 2, 2)
            
            return improvements
            
        except Exception as e:
            logger.error(f"Error calculating quality improvement: {str(e)}")
            return {"completeness": 0.0, "uniqueness": 0.0, "overall": 0.0}
    
    def _infer_best_type(self, series: pd.Series) -> str:
        """Infer the best data type for a series"""
        
        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return str(series.dtype)
        
        # Try numeric conversion
        try:
            pd.to_numeric(non_null_series)
            return "numeric"
        except (ValueError, TypeError):
            pass
        
        # Try datetime conversion
        try:
            pd.to_datetime(non_null_series, infer_datetime_format=True)
            return "datetime"
        except (ValueError, TypeError):
            pass
        
        # Check for boolean
        unique_values = set(str(x).lower() for x in non_null_series.unique())
        if unique_values.issubset({'true', 'false', '1', '0', 'yes', 'no', 't', 'f', 'y', 'n'}):
            return "boolean"
        
        # Check for categorical
        if len(non_null_series.unique()) / len(non_null_series) < 0.5:
            return "category"
        
        return str(series.dtype)
    
    async def _smart_duplicate_detection(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced duplicate detection using ML similarity matching"""
        
        try:
            similarity_threshold = params.get("similarity_threshold", 0.85)
            text_columns = params.get("text_columns", df.select_dtypes(include=['object']).columns.tolist())
            
            def _detect_duplicates():
                duplicates_found = 0
                duplicate_groups = []
                
                if not text_columns:
                    return df, duplicates_found, duplicate_groups
                
                # Create text features for similarity analysis
                text_data = df[text_columns].fillna('').astype(str)
                combined_text = text_data.apply(lambda x: ' '.join(x), axis=1)
                
                if len(combined_text) <= 1:
                    return df, duplicates_found, duplicate_groups
                
                # Use TF-IDF for text similarity
                vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                tfidf_matrix = vectorizer.fit_transform(combined_text)
                
                # Calculate similarity matrix
                similarity_matrix = cosine_similarity(tfidf_matrix)
                
                # Find similar pairs above threshold
                similar_pairs = []
                for i in range(len(similarity_matrix)):
                    for j in range(i + 1, len(similarity_matrix)):
                        if similarity_matrix[i][j] > similarity_threshold:
                            similar_pairs.append((i, j, similarity_matrix[i][j]))
                
                # Group similar records
                groups = {}
                for i, j, sim in similar_pairs:
                    found_group = False
                    for group_id, group in groups.items():
                        if i in group or j in group:
                            group.update([i, j])
                            found_group = True
                            break
                    if not found_group:
                        groups[len(groups)] = {i, j}
                
                # Remove duplicates (keep first in each group)
                rows_to_keep = set(range(len(df)))
                for group in groups.values():
                    group_list = sorted(list(group))
                    # Remove all but the first row in each group
                    for idx in group_list[1:]:
                        rows_to_keep.discard(idx)
                        duplicates_found += 1
                    
                    # Store group info
                    if len(group_list) > 1:
                        duplicate_groups.append({
                            'group_id': len(duplicate_groups),
                            'similarity_score': float(np.mean([
                                similarity_matrix[group_list[i]][group_list[j]]
                                for i in range(len(group_list))
                                for j in range(i + 1, len(group_list))
                            ])),
                            'record_indices': group_list
                        })
                
                cleaned_df = df.iloc[list(rows_to_keep)].reset_index(drop=True)
                return cleaned_df, duplicates_found, duplicate_groups
            
            loop = asyncio.get_event_loop()
            cleaned_df, duplicates_found, duplicate_groups = await loop.run_in_executor(
                self.executor, _detect_duplicates
            )
            
            return {
                "data": cleaned_df,
                "modifications": duplicates_found,
                "summary": {
                    "smart_duplicates_removed": duplicates_found,
                    "similarity_threshold": similarity_threshold,
                    "duplicate_groups_found": len(duplicate_groups),
                    "method": "ml_similarity"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in smart duplicate detection: {str(e)}")
            return {"data": df, "modifications": 0, "summary": {"error": str(e)}}
    
    async def _ml_imputation(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced ML-based imputation using multiple algorithms"""
        
        try:
            columns = params.get("columns", df.columns.tolist())
            method = params.get("method", "iterative")  # iterative, knn, random_forest
            
            def _perform_imputation():
                cleaned_df = df.copy()
                modifications = {}
                
                for col in columns:
                    if col not in df.columns or df[col].isnull().sum() == 0:
                        continue
                    
                    original_missing = df[col].isnull().sum()
                    
                    if pd.api.types.is_numeric_dtype(df[col]):
                        # For numeric columns
                        if method == "iterative":
                            # Use iterative imputer (MICE algorithm)
                            numeric_cols = df.select_dtypes(include=[np.number]).columns
                            if len(numeric_cols) > 1:
                                imputer = IterativeImputer(random_state=42, max_iter=10)
                                imputed_data = imputer.fit_transform(df[numeric_cols])
                                col_idx = list(numeric_cols).index(col)
                                cleaned_df[col] = imputed_data[:, col_idx]
                        elif method == "knn":
                            # Use KNN imputation
                            numeric_cols = df.select_dtypes(include=[np.number]).columns
                            if len(numeric_cols) > 1:
                                imputer = KNNImputer(n_neighbors=5)
                                imputed_data = imputer.fit_transform(df[numeric_cols])
                                col_idx = list(numeric_cols).index(col)
                                cleaned_df[col] = imputed_data[:, col_idx]
                    else:
                        # For categorical columns, use mode or constant
                        mode_value = df[col].mode()
                        if not mode_value.empty:
                            cleaned_df[col].fillna(mode_value.iloc[0], inplace=True)
                    
                    filled_count = original_missing - cleaned_df[col].isnull().sum()
                    modifications[col] = int(filled_count)
                
                return cleaned_df, modifications
            
            loop = asyncio.get_event_loop()
            cleaned_df, modifications = await loop.run_in_executor(
                self.executor, _perform_imputation
            )
            
            total_filled = sum(modifications.values())
            
            return {
                "data": cleaned_df,
                "modifications": total_filled,
                "summary": {
                    "total_filled": total_filled,
                    "method_used": method,
                    "columns_processed": len([col for col in columns if col in modifications]),
                    "by_column": modifications
                }
            }
            
        except Exception as e:
            logger.error(f"Error in ML imputation: {str(e)}")
            return {"data": df, "modifications": 0, "summary": {"error": str(e)}}
    
    async def _anomaly_detection(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced anomaly detection using multiple ML algorithms"""
        
        try:
            contamination = params.get("contamination", 0.1)
            methods = params.get("methods", ["isolation_forest", "local_outlier_factor"])
            
            def _detect_anomalies():
                numeric_df = df.select_dtypes(include=[np.number]).fillna(0)
                if numeric_df.empty:
                    return df, 0, []
                
                anomaly_scores = np.zeros(len(df))
                
                # Isolation Forest
                if "isolation_forest" in methods:
                    iso_forest = IsolationForest(contamination=contamination, random_state=42)
                    iso_scores = iso_forest.fit_predict(numeric_df)
                    anomaly_scores += (iso_scores == -1).astype(int)
                
                # Local Outlier Factor
                if "local_outlier_factor" in methods:
                    from sklearn.neighbors import LocalOutlierFactor
                    lof = LocalOutlierFactor(contamination=contamination)
                    lof_scores = lof.fit_predict(numeric_df)
                    anomaly_scores += (lof_scores == -1).astype(int)
                
                # DBSCAN clustering for anomaly detection
                if "dbscan" in methods:
                    scaler = StandardScaler()
                    scaled_data = scaler.fit_transform(numeric_df)
                    dbscan = DBSCAN(eps=0.5, min_samples=5)
                    cluster_labels = dbscan.fit_predict(scaled_data)
                    anomaly_scores += (cluster_labels == -1).astype(int)
                
                # Consider rows anomalous if detected by majority of methods
                threshold = len([m for m in methods if m in ["isolation_forest", "local_outlier_factor", "dbscan"]]) / 2
                anomaly_mask = anomaly_scores > threshold
                
                anomalies_removed = anomaly_mask.sum()
                anomaly_indices = np.where(anomaly_mask)[0].tolist()
                
                cleaned_df = df[~anomaly_mask].reset_index(drop=True)
                
                return cleaned_df, int(anomalies_removed), anomaly_indices
            
            loop = asyncio.get_event_loop()
            cleaned_df, anomalies_removed, anomaly_indices = await loop.run_in_executor(
                self.executor, _detect_anomalies
            )
            
            return {
                "data": cleaned_df,
                "modifications": anomalies_removed,
                "summary": {
                    "anomalies_removed": anomalies_removed,
                    "methods_used": methods,
                    "contamination": contamination,
                    "anomaly_indices": anomaly_indices[:50]  # Limit to first 50
                }
            }
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}")
            return {"data": df, "modifications": 0, "summary": {"error": str(e)}}
    
    async def _text_standardization(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced text standardization using NLP techniques"""
        
        try:
            columns = params.get("columns", df.select_dtypes(include=['object']).columns.tolist())
            operations = params.get("operations", ["normalize_case", "remove_extra_spaces", "standardize_encoding"])
            
            def _standardize_text():
                cleaned_df = df.copy()
                modifications = {}
                
                for col in columns:
                    if col not in df.columns:
                        continue
                    
                    original_values = cleaned_df[col].copy()
                    changes_made = 0
                    
                    # Convert to string
                    cleaned_df[col] = cleaned_df[col].astype(str)
                    
                    # Normalize case
                    if "normalize_case" in operations:
                        cleaned_df[col] = cleaned_df[col].str.lower()
                    
                    # Remove extra spaces
                    if "remove_extra_spaces" in operations:
                        cleaned_df[col] = cleaned_df[col].str.strip()
                        cleaned_df[col] = cleaned_df[col].str.replace(r'\s+', ' ', regex=True)
                    
                    # Standardize common abbreviations
                    if "standardize_abbreviations" in operations:
                        abbreviations = {
                            r'\bst\b': 'street',
                            r'\bave\b': 'avenue',
                            r'\bdr\b': 'drive',
                            r'\brd\b': 'road',
                            r'\bblvd\b': 'boulevard',
                            r'\bapt\b': 'apartment',
                            r'\bco\b': 'company',
                            r'\binc\b': 'incorporated'
                        }
                        for pattern, replacement in abbreviations.items():
                            cleaned_df[col] = cleaned_df[col].str.replace(pattern, replacement, regex=True)
                    
                    # Remove special characters
                    if "remove_special_chars" in operations:
                        cleaned_df[col] = cleaned_df[col].str.replace(r'[^\w\s]', '', regex=True)
                    
                    # Count changes
                    changes_made = (original_values != cleaned_df[col]).sum()
                    modifications[col] = int(changes_made)
                
                return cleaned_df, modifications
            
            loop = asyncio.get_event_loop()
            cleaned_df, modifications = await loop.run_in_executor(
                self.executor, _standardize_text
            )
            
            total_changes = sum(modifications.values())
            
            return {
                "data": cleaned_df,
                "modifications": total_changes,
                "summary": {
                    "total_changes": total_changes,
                    "operations_applied": operations,
                    "columns_processed": len(columns),
                    "by_column": modifications
                }
            }
            
        except Exception as e:
            logger.error(f"Error in text standardization: {str(e)}")
            return {"data": df, "modifications": 0, "summary": {"error": str(e)}}
    
    async def _auto_encoding_detection(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-detect and fix encoding issues"""
        
        try:
            columns = params.get("columns", df.select_dtypes(include=['object']).columns.tolist())
            
            def _fix_encoding():
                cleaned_df = df.copy()
                encoding_fixes = {}
                
                for col in columns:
                    if col not in df.columns:
                        continue
                    
                    fixes_made = 0
                    original_values = cleaned_df[col].copy()
                    
                    # Convert to string and handle common encoding issues
                    text_series = cleaned_df[col].astype(str)
                    
                    # Fix common encoding issues
                    encoding_fixes_map = {
                        'â€™': "'",  # Smart quote
                        'â€œ': '"',  # Smart quote
                        'â€': '"',   # Smart quote
                        'â€"': '—',  # Em dash
                        'â€"': '–',  # En dash
                        'Ã¡': 'á',   # Latin small letter a with acute
                        'Ã©': 'é',   # Latin small letter e with acute
                        'Ã­': 'í',   # Latin small letter i with acute
                        'Ã³': 'ó',   # Latin small letter o with acute
                        'Ãº': 'ú',   # Latin small letter u with acute
                        'Ã±': 'ñ',   # Latin small letter n with tilde
                        'Ã¼': 'ü',   # Latin small letter u with diaeresis
                    }
                    
                    for bad_encoding, correct_char in encoding_fixes_map.items():
                        text_series = text_series.str.replace(bad_encoding, correct_char)
                    
                    # Count fixes made
                    fixes_made = (original_values != text_series).sum()
                    if fixes_made > 0:
                        cleaned_df[col] = text_series
                        encoding_fixes[col] = int(fixes_made)
                
                return cleaned_df, encoding_fixes
            
            loop = asyncio.get_event_loop()
            cleaned_df, encoding_fixes = await loop.run_in_executor(
                self.executor, _fix_encoding
            )
            
            total_fixes = sum(encoding_fixes.values())
            
            return {
                "data": cleaned_df,
                "modifications": total_fixes,
                "summary": {
                    "encoding_fixes": total_fixes,
                    "columns_processed": len(columns),
                    "fixes_by_column": encoding_fixes
                }
            }
            
        except Exception as e:
            logger.error(f"Error in encoding detection: {str(e)}")
            return {"data": df, "modifications": 0, "summary": {"error": str(e)}}