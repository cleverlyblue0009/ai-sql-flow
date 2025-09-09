"""
Settings and configuration management service
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from ..database import User, Connection, ConnectionType, settings
from ..migration.services import ConnectionService

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for managing application settings and configurations"""
    
    def __init__(self):
        self.connection_service = ConnectionService()
        
        # Default AI configuration
        self.ai_config = {
            "data_quality_models": {
                "anomaly_detection": {
                    "enabled": True,
                    "confidence_threshold": 0.85,
                    "contamination": 0.1
                },
                "semantic_validation": {
                    "enabled": True,
                    "similarity_threshold": 0.9
                },
                "pattern_recognition": {
                    "enabled": True,
                    "auto_detect": True
                }
            },
            "sql_translation_models": {
                "syntax_translation": {
                    "enabled": True,
                    "confidence_threshold": 0.8
                },
                "performance_optimization": {
                    "enabled": True,
                    "optimization_level": "standard"
                },
                "semantic_preservation": {
                    "enabled": True,
                    "maintain_query_meaning": True
                }
            },
            "processing_thresholds": {
                "confidence_threshold": 85,
                "processing_timeout": 300,
                "batch_size": 10000
            }
        }
        
        # Integration configurations
        self.integrations = {
            "slack": {
                "status": "connected",
                "webhook_url": "https://hooks.slack.com/services/...",
                "enabled_notifications": ["alerts", "job_completion"]
            },
            "email_smtp": {
                "status": "connected",
                "server": "smtp.company.com",
                "port": 587,
                "enabled_notifications": ["alerts", "reports"]
            },
            "webhook": {
                "status": "configured",
                "endpoints": [
                    {"name": "Quality Alerts", "url": "https://api.company.com/quality-alerts"},
                    {"name": "Migration Updates", "url": "https://api.company.com/migration-updates"}
                ]
            },
            "jira": {
                "status": "disconnected",
                "server_url": "",
                "enabled": False
            }
        }
        
        # Security settings
        self.security_settings = {
            "security_settings": {
                "two_factor_authentication": True,
                "api_rate_limiting": True,
                "audit_logging": True,
                "session_timeout": 3600
            },
            "compliance": {
                "gdpr_compliance": True,
                "soc2_type_ii": True,
                "hipaa_compliance": False
            },
            "encryption": {
                "data_at_rest": True,
                "data_in_transit": True,
                "key_rotation_days": 90
            },
            "access_control": {
                "role_based_access": True,
                "ip_whitelist_enabled": False,
                "mfa_required": True
            }
        }
    
    async def get_user_connections(self, user_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get all database connections for a user"""
        
        try:
            connections = db.query(Connection).filter(
                Connection.user_id == user_id,
                Connection.is_active == True
            ).all()
            
            result = []
            for conn in connections:
                # Don't include sensitive information
                result.append({
                    "id": conn.id,
                    "name": conn.name,
                    "connection_type": conn.connection_type.value,
                    "host": conn.host,
                    "port": conn.port,
                    "database_name": conn.database_name,
                    "username": conn.username,
                    "created_at": conn.created_at.isoformat(),
                    "last_tested": conn.last_tested.isoformat() if conn.last_tested else None,
                    "test_result": conn.test_result,
                    "status": "connected" if conn.test_result.get("status") == "success" else "error"
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user connections: {str(e)}")
            raise
    
    async def create_connection(self, user_id: int, connection_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Create a new database connection"""
        
        try:
            # Validate required fields
            required_fields = ["name", "connection_type", "host", "port", "database", "username", "password"]
            for field in required_fields:
                if field not in connection_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create connection using migration service
            connection = await self.connection_service.create_or_get_connection(
                db=db,
                user_id=user_id,
                name=connection_data["name"],
                connection_type=connection_data["connection_type"],
                host=connection_data["host"],
                port=connection_data["port"],
                database=connection_data["database"],
                username=connection_data["username"],
                password=connection_data["password"],
                connection_params=connection_data.get("connection_params", {})
            )
            
            return {
                "id": connection.id,
                "name": connection.name,
                "connection_type": connection.connection_type.value,
                "host": connection.host,
                "port": connection.port,
                "database_name": connection.database_name,
                "username": connection.username,
                "created_at": connection.created_at.isoformat(),
                "status": "connected"
            }
            
        except Exception as e:
            logger.error(f"Error creating connection: {str(e)}")
            raise
    
    async def update_connection(self, connection_id: int, user_id: int, connection_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Update an existing database connection"""
        
        try:
            connection = db.query(Connection).filter(
                Connection.id == connection_id,
                Connection.user_id == user_id
            ).first()
            
            if not connection:
                raise ValueError("Connection not found")
            
            # Update fields
            if "name" in connection_data:
                connection.name = connection_data["name"]
            if "host" in connection_data:
                connection.host = connection_data["host"]
            if "port" in connection_data:
                connection.port = connection_data["port"]
            if "database" in connection_data:
                connection.database_name = connection_data["database"]
            if "username" in connection_data:
                connection.username = connection_data["username"]
            if "password" in connection_data:
                # Encrypt password
                cipher = Fernet(settings.encryption_key.encode())
                connection.encrypted_password = cipher.encrypt(connection_data["password"].encode())
            if "connection_params" in connection_data:
                connection.connection_params = connection_data["connection_params"]
            
            connection.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(connection)
            
            return {
                "id": connection.id,
                "name": connection.name,
                "connection_type": connection.connection_type.value,
                "host": connection.host,
                "port": connection.port,
                "database_name": connection.database_name,
                "username": connection.username,
                "updated_at": connection.updated_at.isoformat(),
                "status": "updated"
            }
            
        except Exception as e:
            logger.error(f"Error updating connection: {str(e)}")
            raise
    
    async def delete_connection(self, connection_id: int, user_id: int, db: Session) -> bool:
        """Delete a database connection"""
        
        try:
            connection = db.query(Connection).filter(
                Connection.id == connection_id,
                Connection.user_id == user_id
            ).first()
            
            if not connection:
                return False
            
            # Soft delete by marking as inactive
            connection.is_active = False
            connection.updated_at = datetime.utcnow()
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting connection: {str(e)}")
            raise
    
    async def test_connection(self, connection_id: int, user_id: int, db: Session) -> Dict[str, Any]:
        """Test a database connection"""
        
        try:
            connection = db.query(Connection).filter(
                Connection.id == connection_id,
                Connection.user_id == user_id
            ).first()
            
            if not connection:
                raise ValueError("Connection not found")
            
            # Decrypt password
            cipher = Fernet(settings.encryption_key.encode())
            password = cipher.decrypt(connection.encrypted_password).decode()
            
            # Test connection using migration service
            result = await self.connection_service.test_connection(
                connection_type=connection.connection_type.value,
                host=connection.host,
                port=connection.port,
                database=connection.database_name,
                username=connection.username,
                password=password,
                connection_params=connection.connection_params
            )
            
            # Update test result in database
            connection.last_tested = datetime.utcnow()
            connection.test_result = {
                "status": "success" if result.success else "failed",
                "message": result.message,
                "response_time_ms": result.response_time_ms,
                "database_version": result.database_version,
                "error_details": result.error_details
            }
            db.commit()
            
            return {
                "success": result.success,
                "message": result.message,
                "response_time_ms": result.response_time_ms,
                "database_version": result.database_version,
                "schema_count": result.schema_count,
                "table_count": result.table_count,
                "error_details": result.error_details,
                "tested_at": connection.last_tested.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            raise
    
    async def get_all_users(self, db: Session) -> List[Dict[str, Any]]:
        """Get all users for management (admin only)"""
        
        try:
            users = db.query(User).all()
            
            result = []
            for user in users:
                result.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_active": user.is_active,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "role": "Admin" if user.is_admin else "User"
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}")
            raise
    
    async def update_user_role(self, user_id: int, role: str, db: Session) -> bool:
        """Update user role"""
        
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            if role.lower() == "admin":
                user.is_admin = True
            else:
                user.is_admin = False
            
            user.updated_at = datetime.utcnow()
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating user role: {str(e)}")
            raise
    
    async def get_ai_configuration(self) -> Dict[str, Any]:
        """Get AI model configuration"""
        
        return self.ai_config
    
    async def update_ai_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update AI model configuration"""
        
        try:
            # Update configuration (in production, this would be stored in database)
            self.ai_config.update(config_data)
            return self.ai_config
            
        except Exception as e:
            logger.error(f"Error updating AI configuration: {str(e)}")
            raise
    
    async def get_integrations(self) -> Dict[str, Any]:
        """Get external integrations configuration"""
        
        return self.integrations
    
    async def update_integration(self, integration_name: str, integration_data: Dict[str, Any]) -> bool:
        """Update integration configuration"""
        
        try:
            if integration_name not in self.integrations:
                return False
            
            self.integrations[integration_name].update(integration_data)
            return True
            
        except Exception as e:
            logger.error(f"Error updating integration: {str(e)}")
            raise
    
    async def get_security_settings(self) -> Dict[str, Any]:
        """Get security and compliance settings"""
        
        return self.security_settings
    
    async def update_security_settings(self, security_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update security and compliance settings"""
        
        try:
            # Update security settings (in production, this would be stored in database)
            if "security_settings" in security_data:
                self.security_settings["security_settings"].update(security_data["security_settings"])
            
            if "compliance" in security_data:
                self.security_settings["compliance"].update(security_data["compliance"])
            
            if "encryption" in security_data:
                self.security_settings["encryption"].update(security_data["encryption"])
            
            if "access_control" in security_data:
                self.security_settings["access_control"].update(security_data["access_control"])
            
            return self.security_settings
            
        except Exception as e:
            logger.error(f"Error updating security settings: {str(e)}")
            raise