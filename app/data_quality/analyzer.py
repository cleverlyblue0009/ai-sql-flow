import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime
import logging

from .schemas import (
    ColumnProfile, DataQualityMetrics, DuplicateAnalysis, OutlierAnalysis,
    MissingValueAnalysis, PatternAnalysis, AIRecommendations
)

logger = logging.getLogger(__name__)


class DataQualityAnalyzer:
    """AI-powered data quality analyzer"""
    
    def __init__(self):
        self.similarity_threshold = 0.85
        self.outlier_contamination = 0.1
        
    def analyze_data_quality(
        self, 
        df: pd.DataFrame, 
        ai_enabled: bool = True,
        sample_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Comprehensive data quality analysis"""
        
        try:
            # Sample data if needed
            if sample_size and len(df) > sample_size:
                df_sample = df.sample(n=sample_size, random_state=42)
            else:
                df_sample = df.copy()
            
            logger.info(f"Analyzing data quality for {len(df)} rows, {len(df.columns)} columns")
            
            # Basic profiling
            column_profiles = self._profile_columns(df_sample)
            
            # Quality metrics
            quality_metrics = self._calculate_quality_metrics(df_sample)
            
            # Advanced analysis
            duplicate_analysis = None
            outlier_analysis = None
            missing_analysis = None
            pattern_analysis = None
            ai_recommendations = None
            
            if ai_enabled:
                duplicate_analysis = self._analyze_duplicates(df_sample)
                outlier_analysis = self._analyze_outliers(df_sample)
                missing_analysis = self._analyze_missing_values(df_sample)
                pattern_analysis = self._analyze_patterns(df_sample)
                ai_recommendations = self._generate_ai_recommendations(
                    df_sample, column_profiles, quality_metrics
                )
            
            return {
                "column_profiles": column_profiles,
                "quality_metrics": quality_metrics,
                "duplicate_analysis": duplicate_analysis,
                "outlier_analysis": outlier_analysis,
                "missing_value_analysis": missing_analysis,
                "pattern_analysis": pattern_analysis,
                "ai_recommendations": ai_recommendations
            }
            
        except Exception as e:
            logger.error(f"Error in data quality analysis: {str(e)}")
            raise
    
    def _profile_columns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Profile individual columns"""
        
        profiles = []
        
        for col in df.columns:
            series = df[col]
            
            # Basic statistics
            null_count = series.isnull().sum()
            null_percentage = (null_count / len(series)) * 100
            unique_count = series.nunique()
            unique_percentage = (unique_count / len(series)) * 100
            
            # Data type inference
            inferred_type = self._infer_data_type(series)
            
            # Statistical measures for numeric columns
            min_val = max_val = mean_val = median_val = std_val = None
            if pd.api.types.is_numeric_dtype(series):
                min_val = float(series.min()) if not pd.isna(series.min()) else None
                max_val = float(series.max()) if not pd.isna(series.max()) else None
                mean_val = float(series.mean()) if not pd.isna(series.mean()) else None
                median_val = float(series.median()) if not pd.isna(series.median()) else None
                std_val = float(series.std()) if not pd.isna(series.std()) else None
            
            # Mode value
            mode_val = None
            try:
                mode_series = series.mode()
                if not mode_series.empty:
                    mode_val = str(mode_series.iloc[0])
            except Exception:
                pass
            
            # Pattern analysis for text columns
            pattern_matches = None
            if pd.api.types.is_object_dtype(series):
                pattern_matches = self._analyze_text_patterns(series)
            
            # Sample values
            sample_values = []
            non_null_values = series.dropna()
            if not non_null_values.empty:
                sample_size = min(10, len(non_null_values))
                sample_values = [str(val) for val in non_null_values.head(sample_size).tolist()]
            
            profile = ColumnProfile(
                name=col,
                data_type=str(series.dtype),
                inferred_type=inferred_type,
                null_count=int(null_count),
                null_percentage=round(null_percentage, 2),
                unique_count=int(unique_count),
                unique_percentage=round(unique_percentage, 2),
                min_value=min_val,
                max_value=max_val,
                mean_value=mean_val,
                median_value=median_val,
                mode_value=mode_val,
                std_deviation=std_val,
                pattern_matches=pattern_matches,
                sample_values=sample_values
            )
            
            profiles.append(profile.dict())
        
        return profiles
    
    def _calculate_quality_metrics(self, df: pd.DataFrame) -> DataQualityMetrics:
        """Calculate overall data quality metrics"""
        
        total_cells = df.size
        
        # Completeness: percentage of non-null values
        non_null_cells = df.count().sum()
        completeness = (non_null_cells / total_cells) * 100
        
        # Validity: percentage of values that match expected patterns/types
        validity_score = self._calculate_validity_score(df)
        
        # Uniqueness: measure of duplicate records
        duplicate_rows = len(df) - len(df.drop_duplicates())
        uniqueness = ((len(df) - duplicate_rows) / len(df)) * 100
        
        # Consistency: measure of format consistency within columns
        consistency_score = self._calculate_consistency_score(df)
        
        # Accuracy: estimated based on outliers and pattern matching
        accuracy_score = self._calculate_accuracy_score(df)
        
        # Overall quality score (weighted average)
        overall_score = (
            completeness * 0.25 +
            validity_score * 0.25 +
            uniqueness * 0.2 +
            consistency_score * 0.15 +
            accuracy_score * 0.15
        )
        
        return DataQualityMetrics(
            completeness_score=round(completeness, 2),
            accuracy_score=round(accuracy_score, 2),
            consistency_score=round(consistency_score, 2),
            validity_score=round(validity_score, 2),
            uniqueness_score=round(uniqueness, 2),
            overall_quality_score=round(overall_score, 2)
        )
    
    def _analyze_duplicates(self, df: pd.DataFrame) -> DuplicateAnalysis:
        """AI-powered duplicate detection"""
        
        try:
            # Exact duplicates
            exact_duplicates = df.duplicated().sum()
            
            # Fuzzy duplicates using text similarity for string columns
            fuzzy_duplicates = 0
            duplicate_groups = []
            
            # Identify text columns for fuzzy matching
            text_columns = df.select_dtypes(include=['object']).columns
            
            if len(text_columns) > 0:
                # Create text features for similarity analysis
                text_data = df[text_columns].fillna('').astype(str)
                combined_text = text_data.apply(lambda x: ' '.join(x), axis=1)
                
                if len(combined_text) > 1:
                    # Use TF-IDF for text similarity
                    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                    tfidf_matrix = vectorizer.fit_transform(combined_text)
                    
                    # Calculate similarity matrix
                    similarity_matrix = cosine_similarity(tfidf_matrix)
                    
                    # Find similar pairs above threshold
                    similar_pairs = []
                    for i in range(len(similarity_matrix)):
                        for j in range(i + 1, len(similarity_matrix)):
                            if similarity_matrix[i][j] > self.similarity_threshold:
                                similar_pairs.append((i, j, similarity_matrix[i][j]))
                    
                    # Group similar records
                    groups = {}
                    for i, j, sim in similar_pairs:
                        if i not in groups and j not in groups:
                            groups[len(groups)] = [i, j]
                        elif i in groups:
                            for group_id, group in groups.items():
                                if i in group:
                                    group.append(j)
                                    break
                        elif j in groups:
                            for group_id, group in groups.items():
                                if j in group:
                                    group.append(i)
                                    break
                    
                    # Format duplicate groups
                    for group_id, indices in groups.items():
                        group_data = []
                        for idx in indices:
                            row_data = df.iloc[idx].to_dict()
                            row_data['row_index'] = idx
                            group_data.append(row_data)
                        
                        duplicate_groups.append({
                            'group_id': group_id,
                            'similarity_score': float(np.mean([
                                similarity_matrix[indices[i]][indices[j]]
                                for i in range(len(indices))
                                for j in range(i + 1, len(indices))
                            ])),
                            'records': group_data[:5]  # Limit to first 5 records
                        })
                    
                    fuzzy_duplicates = sum(len(group) - 1 for group in groups.values())
            
            total_duplicates = exact_duplicates + fuzzy_duplicates
            duplicate_percentage = (total_duplicates / len(df)) * 100
            
            return DuplicateAnalysis(
                total_duplicates=int(total_duplicates),
                duplicate_percentage=round(duplicate_percentage, 2),
                duplicate_groups=duplicate_groups[:10],  # Limit to top 10 groups
                similarity_threshold=self.similarity_threshold,
                ai_confidence=0.85 if len(text_columns) > 0 else 0.95
            )
            
        except Exception as e:
            logger.error(f"Error in duplicate analysis: {str(e)}")
            return DuplicateAnalysis(
                total_duplicates=0,
                duplicate_percentage=0.0,
                duplicate_groups=[],
                similarity_threshold=self.similarity_threshold,
                ai_confidence=0.0
            )
    
    def _analyze_outliers(self, df: pd.DataFrame) -> OutlierAnalysis:
        """AI-powered outlier detection"""
        
        try:
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            outliers_by_column = {}
            total_outliers = 0
            
            for col in numeric_columns:
                series = df[col].dropna()
                if len(series) < 10:  # Skip if too few values
                    continue
                
                column_outliers = []
                
                # Statistical outliers (IQR method)
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                stat_outliers = series[(series < lower_bound) | (series > upper_bound)]
                
                # ML-based outliers (Isolation Forest)
                ml_outliers = pd.Series(dtype=float)
                try:
                    if len(series) >= 100:  # Use ML only for larger datasets
                        isolation_forest = IsolationForest(
                            contamination=self.outlier_contamination,
                            random_state=42
                        )
                        outlier_labels = isolation_forest.fit_predict(series.values.reshape(-1, 1))
                        ml_outlier_indices = np.where(outlier_labels == -1)[0]
                        ml_outliers = series.iloc[ml_outlier_indices]
                except Exception:
                    pass
                
                # Combine outliers
                all_outliers = pd.concat([stat_outliers, ml_outliers]).drop_duplicates()
                
                if not all_outliers.empty:
                    for idx, value in all_outliers.items():
                        column_outliers.append({
                            'row_index': int(idx),
                            'value': float(value),
                            'z_score': float(abs((value - series.mean()) / series.std())),
                            'detection_method': 'statistical' if idx in stat_outliers.index else 'ml'
                        })
                    
                    outliers_by_column[col] = column_outliers[:20]  # Limit to top 20
                    total_outliers += len(all_outliers)
            
            outlier_percentage = (total_outliers / len(df)) * 100
            detection_methods = ['statistical', 'isolation_forest']
            
            return OutlierAnalysis(
                total_outliers=int(total_outliers),
                outlier_percentage=round(outlier_percentage, 2),
                outliers_by_column=outliers_by_column,
                detection_methods=detection_methods,
                ai_confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Error in outlier analysis: {str(e)}")
            return OutlierAnalysis(
                total_outliers=0,
                outlier_percentage=0.0,
                outliers_by_column={},
                detection_methods=[],
                ai_confidence=0.0
            )
    
    def _analyze_missing_values(self, df: pd.DataFrame) -> MissingValueAnalysis:
        """Analyze missing value patterns and suggest imputation methods"""
        
        try:
            total_missing = df.isnull().sum().sum()
            missing_percentage = (total_missing / df.size) * 100
            
            missing_by_column = {}
            for col in df.columns:
                missing_count = df[col].isnull().sum()
                if missing_count > 0:
                    missing_by_column[col] = {
                        'count': int(missing_count),
                        'percentage': round((missing_count / len(df)) * 100, 2),
                        'missing_indices': df[df[col].isnull()].index.tolist()[:10]  # First 10
                    }
            
            # Analyze missing patterns
            missing_patterns = []
            missing_pattern_df = df.isnull()
            pattern_counts = missing_pattern_df.value_counts()
            
            for pattern, count in pattern_counts.head(5).items():
                missing_cols = [col for col, is_missing in zip(df.columns, pattern) if is_missing]
                missing_patterns.append({
                    'pattern': missing_cols,
                    'count': int(count),
                    'percentage': round((count / len(df)) * 100, 2)
                })
            
            # Suggest imputation methods
            imputation_suggestions = {}
            for col in df.columns:
                if df[col].isnull().sum() > 0:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        if df[col].nunique() < 10:
                            imputation_suggestions[col] = "mode"
                        else:
                            imputation_suggestions[col] = "median"
                    else:
                        imputation_suggestions[col] = "mode"
            
            return MissingValueAnalysis(
                total_missing=int(total_missing),
                missing_percentage=round(missing_percentage, 2),
                missing_by_column=missing_by_column,
                missing_patterns=missing_patterns,
                imputation_suggestions=imputation_suggestions
            )
            
        except Exception as e:
            logger.error(f"Error in missing value analysis: {str(e)}")
            return MissingValueAnalysis(
                total_missing=0,
                missing_percentage=0.0,
                missing_by_column={},
                missing_patterns=[],
                imputation_suggestions={}
            )
    
    def _analyze_patterns(self, df: pd.DataFrame) -> PatternAnalysis:
        """Analyze data patterns and formats"""
        
        try:
            detected_patterns = {}
            format_consistency = {}
            regex_patterns = {}
            
            text_columns = df.select_dtypes(include=['object']).columns
            
            for col in text_columns:
                series = df[col].dropna().astype(str)
                if len(series) == 0:
                    continue
                
                # Common patterns
                patterns = {
                    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                    'phone': r'^[\+]?[1-9]?[0-9]{7,15}$',
                    'url': r'^https?://[^\s/$.?#].[^\s]*$',
                    'date': r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',
                    'credit_card': r'^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$',
                    'ssn': r'^\d{3}-\d{2}-\d{4}$',
                    'zip_code': r'^\d{5}(-\d{4})?$'
                }
                
                column_patterns = []
                for pattern_name, pattern_regex in patterns.items():
                    matches = series.str.match(pattern_regex).sum()
                    if matches > 0:
                        column_patterns.append({
                            'pattern': pattern_name,
                            'matches': int(matches),
                            'percentage': round((matches / len(series)) * 100, 2)
                        })
                
                if column_patterns:
                    detected_patterns[col] = column_patterns
                
                # Format consistency
                unique_formats = set()
                for value in series.head(100):  # Sample first 100 values
                    format_pattern = re.sub(r'\d', 'N', str(value))
                    format_pattern = re.sub(r'[a-zA-Z]', 'A', format_pattern)
                    unique_formats.add(format_pattern)
                
                consistency_score = 1.0 / len(unique_formats) if unique_formats else 0.0
                format_consistency[col] = round(consistency_score * 100, 2)
                
                # Generate regex pattern for most common format
                if unique_formats:
                    most_common_format = max(unique_formats, key=lambda x: sum(
                        1 for val in series.head(100) 
                        if re.sub(r'\d', 'N', re.sub(r'[a-zA-Z]', 'A', str(val))) == x
                    ))
                    regex_patterns[col] = most_common_format
            
            return PatternAnalysis(
                detected_patterns=detected_patterns,
                format_consistency=format_consistency,
                regex_patterns=regex_patterns,
                ai_suggestions={
                    'standardization_needed': [
                        col for col, score in format_consistency.items() if score < 80
                    ],
                    'validation_rules': list(detected_patterns.keys())
                }
            )
            
        except Exception as e:
            logger.error(f"Error in pattern analysis: {str(e)}")
            return PatternAnalysis(
                detected_patterns={},
                format_consistency={},
                regex_patterns={},
                ai_suggestions={}
            )
    
    def _generate_ai_recommendations(
        self, 
        df: pd.DataFrame, 
        column_profiles: List[Dict], 
        quality_metrics: DataQualityMetrics
    ) -> AIRecommendations:
        """Generate AI-powered data quality recommendations"""
        
        try:
            data_type_corrections = {}
            cleaning_priority = []
            quality_improvements = []
            automation_suggestions = []
            confidence_scores = {}
            
            # Data type corrections
            for profile in column_profiles:
                col_name = profile['name']
                current_type = profile['data_type']
                inferred_type = profile['inferred_type']
                
                if inferred_type and inferred_type != current_type:
                    data_type_corrections[col_name] = inferred_type
                    confidence_scores[f"type_correction_{col_name}"] = 0.8
            
            # Cleaning priority based on impact
            if quality_metrics.completeness_score < 90:
                cleaning_priority.append({
                    'issue': 'missing_values',
                    'priority': 'high',
                    'impact': 'completeness',
                    'estimated_improvement': 90 - quality_metrics.completeness_score
                })
            
            if quality_metrics.uniqueness_score < 95:
                cleaning_priority.append({
                    'issue': 'duplicates',
                    'priority': 'medium',
                    'impact': 'uniqueness',
                    'estimated_improvement': 95 - quality_metrics.uniqueness_score
                })
            
            if quality_metrics.consistency_score < 85:
                cleaning_priority.append({
                    'issue': 'format_inconsistency',
                    'priority': 'medium',
                    'impact': 'consistency',
                    'estimated_improvement': 85 - quality_metrics.consistency_score
                })
            
            # Quality improvements
            if quality_metrics.overall_quality_score < 80:
                quality_improvements.append({
                    'recommendation': 'comprehensive_cleaning',
                    'description': 'Perform full data cleaning pipeline including deduplication, missing value imputation, and format standardization',
                    'expected_improvement': 15
                })
            
            # Automation suggestions
            if len(data_type_corrections) > 0:
                automation_suggestions.append("Automated data type conversion")
            
            if any(profile['null_percentage'] > 20 for profile in column_profiles):
                automation_suggestions.append("Automated missing value imputation")
            
            if quality_metrics.uniqueness_score < 95:
                automation_suggestions.append("Automated duplicate detection and removal")
            
            return AIRecommendations(
                data_type_corrections=data_type_corrections,
                cleaning_priority=cleaning_priority,
                quality_improvements=quality_improvements,
                automation_suggestions=automation_suggestions,
                confidence_scores=confidence_scores
            )
            
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {str(e)}")
            return AIRecommendations(
                data_type_corrections={},
                cleaning_priority=[],
                quality_improvements=[],
                automation_suggestions=[],
                confidence_scores={}
            )
    
    def _infer_data_type(self, series: pd.Series) -> str:
        """Infer the most appropriate data type for a column"""
        
        non_null_series = series.dropna()
        if len(non_null_series) == 0:
            return "unknown"
        
        # Try to convert to numeric
        try:
            pd.to_numeric(non_null_series)
            if all(float(x).is_integer() for x in non_null_series if pd.notna(x)):
                return "integer"
            else:
                return "float"
        except (ValueError, TypeError):
            pass
        
        # Try to convert to datetime
        try:
            pd.to_datetime(non_null_series, infer_datetime_format=True)
            return "datetime"
        except (ValueError, TypeError):
            pass
        
        # Check for boolean
        unique_values = set(str(x).lower() for x in non_null_series.unique())
        if unique_values.issubset({'true', 'false', '1', '0', 'yes', 'no', 't', 'f', 'y', 'n'}):
            return "boolean"
        
        # Check for categorical (if unique values are less than 50% of total)
        if len(non_null_series.unique()) / len(non_null_series) < 0.5:
            return "categorical"
        
        return "text"
    
    def _analyze_text_patterns(self, series: pd.Series) -> Dict[str, int]:
        """Analyze patterns in text data"""
        
        patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^[\+]?[1-9]?[0-9]{7,15}$',
            'url': r'^https?://[^\s/$.?#].[^\s]*$',
            'numeric': r'^\d+$',
            'alphanumeric': r'^[a-zA-Z0-9]+$',
            'contains_special': r'[^a-zA-Z0-9\s]'
        }
        
        results = {}
        non_null_series = series.dropna().astype(str)
        
        for pattern_name, pattern_regex in patterns.items():
            matches = non_null_series.str.match(pattern_regex).sum()
            if matches > 0:
                results[pattern_name] = int(matches)
        
        return results
    
    def _calculate_validity_score(self, df: pd.DataFrame) -> float:
        """Calculate validity score based on data type consistency"""
        
        total_score = 0
        total_columns = 0
        
        for col in df.columns:
            series = df[col].dropna()
            if len(series) == 0:
                continue
            
            inferred_type = self._infer_data_type(series)
            current_type = str(series.dtype)
            
            # Score based on type consistency
            if inferred_type == "integer" and "int" in current_type:
                score = 100
            elif inferred_type == "float" and "float" in current_type:
                score = 100
            elif inferred_type == "datetime" and "datetime" in current_type:
                score = 100
            elif inferred_type == "boolean" and "bool" in current_type:
                score = 100
            elif inferred_type in ["text", "categorical"] and "object" in current_type:
                score = 80  # Text data is harder to validate
            else:
                score = 60  # Type mismatch
            
            total_score += score
            total_columns += 1
        
        return total_score / total_columns if total_columns > 0 else 0
    
    def _calculate_consistency_score(self, df: pd.DataFrame) -> float:
        """Calculate consistency score based on format consistency"""
        
        text_columns = df.select_dtypes(include=['object']).columns
        if len(text_columns) == 0:
            return 100
        
        total_score = 0
        
        for col in text_columns:
            series = df[col].dropna().astype(str)
            if len(series) == 0:
                continue
            
            # Calculate format consistency
            unique_formats = set()
            for value in series:
                format_pattern = re.sub(r'\d', 'N', str(value))
                format_pattern = re.sub(r'[a-zA-Z]', 'A', format_pattern)
                unique_formats.add(format_pattern)
            
            consistency = 1.0 / len(unique_formats) if unique_formats else 0.0
            total_score += consistency * 100
        
        return total_score / len(text_columns)
    
    def _calculate_accuracy_score(self, df: pd.DataFrame) -> float:
        """Estimate accuracy score based on outliers and patterns"""
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) == 0:
            return 85  # Default score for non-numeric data
        
        total_outliers = 0
        total_values = 0
        
        for col in numeric_columns:
            series = df[col].dropna()
            if len(series) < 10:
                continue
            
            # Count statistical outliers
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = series[(series < lower_bound) | (series > upper_bound)]
            total_outliers += len(outliers)
            total_values += len(series)
        
        if total_values == 0:
            return 85
        
        outlier_percentage = (total_outliers / total_values) * 100
        accuracy_score = max(0, 100 - outlier_percentage * 2)  # Penalize outliers
        
        return accuracy_score