from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json
from datetime import datetime

from ..database.models import AuditLog


async def log_user_action(
    db: Session,
    user_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_method: Optional[str] = None,
    request_path: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> AuditLog:
    """Log user action for audit trail"""
    
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method=request_method,
        request_path=request_path,
        details=details,
        success=success,
        error_message=error_message
    )
    
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    
    return audit_log


def log_data_quality_action(
    db: Session,
    user_id: int,
    action: str,
    project_id: Optional[int] = None,
    job_id: Optional[str] = None,
    file_name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> AuditLog:
    """Log data quality related actions"""
    
    audit_details = {
        "project_id": project_id,
        "job_id": job_id,
        "file_name": file_name,
        **(details or {})
    }
    
    return log_user_action(
        db=db,
        user_id=user_id,
        action=action,
        resource_type="data_quality",
        resource_id=job_id,
        details=audit_details,
        success=success,
        error_message=error_message
    )


def log_migration_action(
    db: Session,
    user_id: int,
    action: str,
    migration_id: Optional[str] = None,
    source_db: Optional[str] = None,
    target_db: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> AuditLog:
    """Log migration related actions"""
    
    audit_details = {
        "migration_id": migration_id,
        "source_db": source_db,
        "target_db": target_db,
        **(details or {})
    }
    
    return log_user_action(
        db=db,
        user_id=user_id,
        action=action,
        resource_type="migration",
        resource_id=migration_id,
        details=audit_details,
        success=success,
        error_message=error_message
    )


def log_connection_action(
    db: Session,
    user_id: int,
    action: str,
    connection_id: Optional[int] = None,
    connection_name: Optional[str] = None,
    connection_type: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> AuditLog:
    """Log database connection related actions"""
    
    audit_details = {
        "connection_id": connection_id,
        "connection_name": connection_name,
        "connection_type": connection_type,
        **(details or {})
    }
    
    return log_user_action(
        db=db,
        user_id=user_id,
        action=action,
        resource_type="connection",
        resource_id=str(connection_id) if connection_id else None,
        details=audit_details,
        success=success,
        error_message=error_message
    )