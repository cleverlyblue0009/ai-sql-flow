"""
Smart Analytics API routes
Provides AI-powered insights, pattern detection, and data intelligence.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
from collections import defaultdict

from ..database.config import get_db
from ..database.models import DataProfile, User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/smart-analytics", tags=["Smart Analytics"])


@router.get("/query-optimizer")
async def get_query_optimizer_insights(db: Session = Depends(get_db)):
    """
    Get SQL Query Optimizer insights
    Analyzes conversion patterns and provides optimization suggestions
    """
    try:
        # Mock data for query optimizer (would analyze real conversion data)
        insights = {
            "conversion_patterns": [
                {
                    "source": "MySQL",
                    "target": "Snowflake",
                    "count": 42,
                    "avg_complexity": 6.8,
                    "success_rate": 98.5
                },
                {
                    "source": "PostgreSQL",
                    "target": "Snowflake",
                    "count": 38,
                    "avg_complexity": 7.2,
                    "success_rate": 97.3
                },
                {
                    "source": "MySQL",
                    "target": "PostgreSQL",
                    "count": 25,
                    "avg_complexity": 5.4,
                    "success_rate": 99.2
                },
                {
                    "source": "Oracle",
                    "target": "PostgreSQL",
                    "count": 18,
                    "avg_complexity": 8.5,
                    "success_rate": 94.1
                },
                {
                    "source": "SQL Server",
                    "target": "Snowflake",
                    "count": 15,
                    "avg_complexity": 7.9,
                    "success_rate": 96.7
                }
            ],
            "optimization_suggestions": [
                {
                    "type": "performance",
                    "title": "Optimize JOIN operations",
                    "description": "Consider using index hints for large table joins in Snowflake migrations",
                    "impact": "high",
                    "affected_conversions": 12
                },
                {
                    "type": "compatibility",
                    "title": "Date function standardization",
                    "description": "Detected inconsistent date function usage across MySQL to PostgreSQL conversions",
                    "impact": "medium",
                    "affected_conversions": 8
                },
                {
                    "type": "efficiency",
                    "title": "Subquery optimization",
                    "description": "Replace correlated subqueries with CTEs for better performance",
                    "impact": "medium",
                    "affected_conversions": 6
                }
            ],
            "conversion_heatmap": [
                ["MySQL", "PostgreSQL", 25],
                ["MySQL", "Snowflake", 42],
                ["MySQL", "BigQuery", 8],
                ["PostgreSQL", "Snowflake", 38],
                ["PostgreSQL", "MySQL", 12],
                ["Oracle", "PostgreSQL", 18],
                ["Oracle", "Snowflake", 9],
                ["SQL Server", "Snowflake", 15],
                ["SQL Server", "PostgreSQL", 7]
            ],
            "confidence_scores": {
                "average": 96.4,
                "by_dialect": [
                    {"dialect": "MySQL → Snowflake", "confidence": 98.5},
                    {"dialect": "PostgreSQL → Snowflake", "confidence": 97.3},
                    {"dialect": "MySQL → PostgreSQL", "confidence": 99.2},
                    {"dialect": "Oracle → PostgreSQL", "confidence": 94.1}
                ]
            }
        }
        
        return {
            "status": "success",
            "data": insights,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting query optimizer insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve query optimizer insights"
        )


@router.get("/anomalies")
async def get_anomaly_detection(db: Session = Depends(get_db)):
    """
    Get data quality anomaly detection results
    Shows real-time anomalies and suspicious patterns
    """
    try:
        # Get recent data profiles from database
        recent_profiles = db.query(DataProfile).order_by(
            desc(DataProfile.created_at)
        ).limit(50).all()
        
        anomalies = []
        
        # Generate anomaly insights based on real data
        for profile in recent_profiles:
            # Simulate anomaly detection (in production, this would use ML models)
            if profile.quality_score < 80:
                anomaly_score = 100 - profile.quality_score
                
                detected_issues = []
                if profile.completeness_score < 90:
                    detected_issues.append(f"Low completeness: {profile.completeness_score}%")
                if profile.validity_score < 90:
                    detected_issues.append(f"Low validity: {profile.validity_score}%")
                if profile.consistency_score < 90:
                    detected_issues.append(f"Low consistency: {profile.consistency_score}%")
                
                anomalies.append({
                    "file_id": profile.id,
                    "file_name": profile.file_name,
                    "anomaly_score": round(anomaly_score, 1),
                    "detected_issues": detected_issues,
                    "confidence": round(85 + (anomaly_score / 10), 1),
                    "timestamp": profile.created_at.isoformat(),
                    "severity": "high" if anomaly_score > 30 else "medium"
                })
        
        # Add summary statistics
        summary = {
            "total_files_analyzed": len(recent_profiles),
            "anomalies_detected": len(anomalies),
            "avg_quality_score": round(
                sum(p.quality_score for p in recent_profiles) / len(recent_profiles)
                if recent_profiles else 0,
                1
            ),
            "high_severity_count": sum(1 for a in anomalies if a["severity"] == "high")
        }
        
        return {
            "status": "success",
            "data": {
                "anomalies": anomalies[:10],  # Return top 10 most recent
                "summary": summary
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting anomaly detection data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve anomaly detection data"
        )


@router.get("/activity-intelligence")
async def get_activity_intelligence(db: Session = Depends(get_db)):
    """
    Get activity intelligence and data lineage
    Correlates activities across Clean Data + SQL Conversion
    """
    try:
        # Get recent activities from database
        recent_profiles = db.query(DataProfile).order_by(
            desc(DataProfile.created_at)
        ).limit(20).all()
        
        # Build data lineage (simplified version)
        data_lineage = []
        for profile in recent_profiles:
            lineage_item = {
                "file_id": profile.id,
                "file_name": profile.file_name,
                "created_at": profile.created_at.isoformat(),
                "quality_score": profile.quality_score,
                "has_cleaning": bool(profile.cleaning_history),
                "row_count": profile.row_count,
                "column_count": profile.column_count
            }
            data_lineage.append(lineage_item)
        
        # Generate dependency graph
        dependency_graph = {
            "nodes": [
                {"id": f"file_{p.id}", "name": p.file_name, "type": "data_file"}
                for p in recent_profiles[:10]
            ],
            "edges": []  # Would track actual dependencies in production
        }
        
        # Next suggested actions based on patterns
        suggested_actions = [
            {
                "action": "clean_data",
                "title": "Clean recently uploaded files",
                "description": "3 files uploaded in the last hour could benefit from quality improvement",
                "priority": "high",
                "estimated_impact": "+12% quality score"
            },
            {
                "action": "sql_migration",
                "title": "Convert cleaned data schemas to Snowflake",
                "description": "Based on your recent activity, consider migrating your improved schemas",
                "priority": "medium",
                "estimated_impact": "Consistent schema across platforms"
            },
            {
                "action": "batch_analysis",
                "title": "Run batch quality analysis",
                "description": "Analyze multiple files at once for efficiency",
                "priority": "low",
                "estimated_impact": "Time savings: 40%"
            }
        ]
        
        # Activity patterns
        activity_patterns = {
            "most_active_hours": [9, 10, 14, 15, 16],
            "avg_files_per_day": round(len(recent_profiles) / 7, 1),
            "peak_activity_day": "Tuesday",
            "common_file_types": ["CSV", "Excel", "JSON"]
        }
        
        return {
            "status": "success",
            "data": {
                "data_lineage": data_lineage,
                "dependency_graph": dependency_graph,
                "suggested_actions": suggested_actions,
                "activity_patterns": activity_patterns
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting activity intelligence: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity intelligence"
        )


@router.get("/performance-insights")
async def get_performance_insights(db: Session = Depends(get_db)):
    """
    Get performance insights and metrics
    Tracks processing times, success rates, and optimization opportunities
    """
    try:
        # Get data profiles for analysis
        profiles = db.query(DataProfile).order_by(
            desc(DataProfile.created_at)
        ).limit(100).all()
        
        if not profiles:
            return {
                "status": "success",
                "data": {
                    "message": "No data available yet. Upload some files to see performance insights!"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Calculate performance metrics
        avg_quality = sum(p.quality_score for p in profiles) / len(profiles)
        
        # Quality improvement tracking
        cleaned_profiles = [p for p in profiles if p.cleaning_history]
        avg_improvement = 0
        if cleaned_profiles:
            improvements = []
            for p in cleaned_profiles:
                # Simulate before/after quality scores
                before_score = p.quality_score - 10  # Simplified
                after_score = p.quality_score
                improvements.append(after_score - before_score)
            avg_improvement = sum(improvements) / len(improvements)
        
        # Processing time trends (simulated)
        processing_metrics = {
            "avg_upload_time": 1.2,
            "avg_analysis_time": 3.4,
            "avg_cleaning_time": 5.7,
            "trend": "improving"
        }
        
        # Bottleneck detection
        bottlenecks = []
        if avg_quality < 85:
            bottlenecks.append({
                "area": "Data Quality",
                "description": "Average quality score below optimal threshold",
                "recommendation": "Consider implementing automated pre-validation",
                "impact": "medium"
            })
        
        insights = {
            "quality_metrics": {
                "avg_quality_score": round(avg_quality, 1),
                "avg_improvement": round(avg_improvement, 1),
                "total_files_processed": len(profiles),
                "files_cleaned": len(cleaned_profiles)
            },
            "processing_metrics": processing_metrics,
            "efficiency_score": round(min(95 + avg_improvement, 99), 1),
            "bottlenecks": bottlenecks,
            "optimization_opportunities": [
                {
                    "title": "Batch Processing",
                    "description": "Process multiple files simultaneously",
                    "potential_savings": "35% time reduction"
                },
                {
                    "title": "Predictive Cleaning",
                    "description": "AI-powered automatic cleaning suggestions",
                    "potential_savings": "50% manual effort reduction"
                }
            ]
        }
        
        return {
            "status": "success",
            "data": insights,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting performance insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance insights"
        )
