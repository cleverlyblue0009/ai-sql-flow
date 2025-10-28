#!/usr/bin/env python3
"""
Mock data generation script for DataFlow AI Enterprise Platform
Generates realistic test data for demonstration purposes
"""

import os
import sys
import random
import csv
import json
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker
from pathlib import Path

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal, create_tables
from app.database.models import (
    User, UserRole, Project, DataProfile, Job, JobStatus, 
    MigrationLog, MigrationStatus, Connection, ConnectionType, AuditLog
)

fake = Faker()

def create_mock_users(db, count=10):
    """Create mock users with Firebase UIDs"""
    users = []
    
    # Create admin user
    admin_user = User(
        email="admin@dataflow.ai",
        username="admin",
        full_name="System Administrator",
        firebase_uid=fake.uuid4(),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow() - timedelta(days=365),
        last_login=datetime.utcnow() - timedelta(hours=2)
    )
    db.add(admin_user)
    users.append(admin_user)
    
    # Create engineer users
    for i in range(3):
        user = User(
            email=f"engineer{i+1}@dataflow.ai",
            username=f"engineer{i+1}",
            full_name=fake.name(),
            firebase_uid=fake.uuid4(),
            role=UserRole.ENGINEER,
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow() - timedelta(days=random.randint(30, 300)),
            last_login=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )
        db.add(user)
        users.append(user)
    
    # Create analyst users
    for i in range(count - 4):
        user = User(
            email=fake.email(),
            username=fake.user_name(),
            full_name=fake.name(),
            firebase_uid=fake.uuid4(),
            role=UserRole.ANALYST,
            is_active=random.choice([True, True, True, False]),  # 75% active
            is_verified=random.choice([True, True, False]),  # 66% verified
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 200)),
            last_login=datetime.utcnow() - timedelta(hours=random.randint(1, 168))
        )
        db.add(user)
        users.append(user)
    
    db.commit()
    print(f"Created {len(users)} mock users")
    return users


def create_mock_projects(db, users, count=20):
    """Create mock projects"""
    projects = []
    
    project_names = [
        "Customer Data Migration", "Sales Analytics Platform", "Inventory Optimization",
        "Financial Reporting System", "User Behavior Analysis", "Product Catalog Cleanup",
        "Order Processing Migration", "Marketing Campaign Data", "Supply Chain Analytics",
        "HR Data Integration", "Quality Assurance Metrics", "Performance Dashboard",
        "Risk Assessment Platform", "Compliance Reporting", "Fraud Detection System",
        "Revenue Analytics", "Customer Segmentation", "Operational Metrics",
        "Data Warehouse Migration", "Real-time Analytics"
    ]
    
    for i in range(count):
        owner = random.choice([u for u in users if u.is_active])
        
        project = Project(
            name=project_names[i] if i < len(project_names) else f"Project {fake.company()}",
            description=fake.text(max_nb_chars=200),
            owner_id=owner.id,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365)),
            is_active=random.choice([True, True, True, False]),  # 75% active
            settings={
                "default_quality_threshold": random.uniform(0.8, 0.95),
                "auto_cleanup": random.choice([True, False]),
                "notification_preferences": {
                    "email": True,
                    "in_app": True,
                    "webhook": random.choice([True, False])
                }
            }
        )
        db.add(project)
        projects.append(project)
    
    db.commit()
    print(f"Created {len(projects)} mock projects")
    return projects


def create_mock_connections(db, users, count=30):
    """Create mock database connections"""
    connections = []
    
    connection_types = [
        ConnectionType.POSTGRESQL,
        ConnectionType.MYSQL,
        ConnectionType.SQLSERVER,
        ConnectionType.ORACLE,
        ConnectionType.MONGODB
    ]
    
    for i in range(count):
        user = random.choice([u for u in users if u.is_active])
        conn_type = random.choice(connection_types)
        
        connection = Connection(
            name=f"{conn_type.value.title()} {fake.company()} DB",
            connection_type=conn_type,
            user_id=user.id,
            host=fake.ipv4_private(),
            port=random.choice([5432, 3306, 1433, 1521, 27017]),
            database_name=fake.word() + "_" + fake.word(),
            username=fake.user_name(),
            encrypted_password=b"encrypted_password_placeholder",
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 180)),
            is_active=random.choice([True, True, False]),  # 66% active
            last_tested=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
            test_result={
                "status": random.choice(["success", "success", "success", "failed"]),
                "response_time_ms": random.uniform(10, 500),
                "message": "Connection test completed"
            },
            connection_params={
                "timeout": 30,
                "pool_size": random.randint(5, 20),
                "ssl": random.choice([True, False])
            }
        )
        db.add(connection)
        connections.append(connection)
    
    db.commit()
    print(f"Created {len(connections)} mock connections")
    return connections


def create_mock_data_profiles(db, projects, count=100):
    """Create mock data profiles"""
    profiles = []
    
    file_types = ["CSV", "Excel", "JSON", "Parquet", "TSV"]
    table_names = [
        "customers", "orders", "products", "transactions", "users", "inventory",
        "sales", "employees", "vendors", "invoices", "payments", "shipments",
        "reviews", "categories", "campaigns", "leads", "accounts", "contacts"
    ]
    
    for i in range(count):
        project = random.choice([p for p in projects if p.is_active])
        file_type = random.choice(file_types)
        table_name = random.choice(table_names)
        
        # Generate realistic quality scores
        completeness = random.uniform(0.7, 0.98)
        accuracy = random.uniform(0.65, 0.95)
        consistency = random.uniform(0.8, 0.99)
        validity = random.uniform(0.6, 0.92)
        uniqueness = random.uniform(0.85, 0.99)
        overall_quality = (completeness + accuracy + consistency + validity + uniqueness) / 5
        
        profile = DataProfile(
            project_id=project.id,
            source_name=f"{table_name}_data.{file_type.lower()}",
            source_type="file",
            file_path=f"data/{project.owner_id}/{project.id}/{fake.uuid4()}_{table_name}.{file_type.lower()}",
            file_size=random.randint(1024, 100 * 1024 * 1024),  # 1KB to 100MB
            column_count=random.randint(5, 50),
            row_count=random.randint(1000, 1000000),
            schema_info={
                "columns": [
                    {
                        "name": fake.word(),
                        "dtype": random.choice(["object", "int64", "float64", "datetime64", "bool"]),
                        "null_count": random.randint(0, 1000),
                        "unique_count": random.randint(100, 10000)
                    }
                    for _ in range(random.randint(5, 15))
                ]
            },
            completeness_score=completeness,
            accuracy_score=accuracy,
            consistency_score=consistency,
            validity_score=validity,
            uniqueness_score=uniqueness,
            overall_quality_score=overall_quality,
            column_profiles={
                "quality_issues": {
                    "duplicates": random.randint(0, 1000),
                    "missing_values": random.randint(0, 500),
                    "outliers": random.randint(0, 100),
                    "format_errors": random.randint(0, 200)
                },
                "data_types": {
                    "numeric": random.randint(1, 10),
                    "text": random.randint(1, 10),
                    "date": random.randint(0, 5),
                    "boolean": random.randint(0, 3)
                }
            },
            ai_recommendations=[
                "Remove duplicate records based on customer ID",
                "Standardize phone number formats",
                "Fill missing email addresses using ML prediction",
                "Validate postal codes against reference data"
            ][:random.randint(1, 4)],
            cleaning_suggestions=[
                {
                    "type": "remove_duplicates",
                    "column": "customer_id",
                    "confidence": random.uniform(0.8, 0.99)
                },
                {
                    "type": "fill_missing",
                    "column": "email",
                    "method": "ml_prediction",
                    "confidence": random.uniform(0.7, 0.9)
                }
            ],
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90))
        )
        db.add(profile)
        profiles.append(profile)
    
    db.commit()
    print(f"Created {len(profiles)} mock data profiles")
    return profiles


def create_mock_migrations(db, projects, connections, count=50):
    """Create mock migration logs"""
    migrations = []
    
    migration_names = [
        "Customer DB Migration to Snowflake",
        "Legacy Oracle to PostgreSQL",
        "MySQL to Cloud Migration",
        "SQL Server Modernization",
        "Data Warehouse Migration",
        "Analytics Platform Upgrade",
        "E-commerce DB Migration",
        "CRM System Migration",
        "ERP Data Migration",
        "Reporting DB Upgrade"
    ]
    
    for i in range(count):
        project = random.choice([p for p in projects if p.is_active])
        source_conn = random.choice(connections)
        target_conn = random.choice([c for c in connections if c.id != source_conn.id])
        
        status = random.choice([
            MigrationStatus.COMPLETED,
            MigrationStatus.COMPLETED,
            MigrationStatus.COMPLETED,
            MigrationStatus.EXECUTING,
            MigrationStatus.TRANSLATING,
            MigrationStatus.FAILED
        ])
        
        created_time = datetime.utcnow() - timedelta(days=random.randint(1, 180))
        started_time = created_time + timedelta(hours=random.randint(1, 24)) if status != MigrationStatus.CREATED else None
        completed_time = started_time + timedelta(hours=random.randint(1, 48)) if status == MigrationStatus.COMPLETED else None
        
        migration = MigrationLog(
            migration_id=fake.uuid4(),
            project_id=project.id,
            source_connection_id=source_conn.id,
            target_connection_id=target_conn.id,
            name=migration_names[i % len(migration_names)],
            description=fake.text(max_nb_chars=150),
            source_dialect=source_conn.connection_type.value,
            target_dialect=target_conn.connection_type.value,
            status=status,
            created_at=created_time,
            started_at=started_time,
            completed_at=completed_time,
            progress_percentage=100.0 if status == MigrationStatus.COMPLETED else random.uniform(10, 90),
            current_phase=status.value,
            schema_mapping={
                "table_mappings": {
                    "old_customers": "customers",
                    "old_orders": "orders",
                    "old_products": "products"
                },
                "column_mappings": {
                    "customer_id": "id",
                    "customer_name": "full_name"
                }
            },
            performance_metrics={
                "query_improvement": random.uniform(30, 80),
                "storage_reduction": random.uniform(15, 50),
                "cost_savings": random.uniform(1000, 10000)
            } if status == MigrationStatus.COMPLETED else None
        )
        db.add(migration)
        migrations.append(migration)
    
    db.commit()
    print(f"Created {len(migrations)} mock migrations")
    return migrations


def create_mock_jobs(db, users, projects, data_profiles, count=200):
    """Create mock jobs"""
    jobs = []
    
    job_types = ["data_upload", "data_analysis", "data_cleaning", "migration", "sql_translation"]
    
    for i in range(count):
        user = random.choice([u for u in users if u.is_active])
        project = random.choice([p for p in projects if p.is_active]) if random.choice([True, False]) else None
        job_type = random.choice(job_types)
        
        status = random.choice([
            JobStatus.COMPLETED,
            JobStatus.COMPLETED,
            JobStatus.COMPLETED,
            JobStatus.RUNNING,
            JobStatus.FAILED,
            JobStatus.PENDING
        ])
        
        created_time = datetime.utcnow() - timedelta(days=random.randint(1, 60))
        started_time = created_time + timedelta(minutes=random.randint(1, 60)) if status != JobStatus.PENDING else None
        completed_time = started_time + timedelta(minutes=random.randint(1, 120)) if status in [JobStatus.COMPLETED, JobStatus.FAILED] else None
        
        job = Job(
            job_id=fake.uuid4(),
            job_type=job_type,
            name=f"{job_type.replace('_', ' ').title()} - {fake.word()}",
            description=fake.sentence(),
            status=status,
            user_id=user.id,
            project_id=project.id if project else None,
            created_at=created_time,
            started_at=started_time,
            completed_at=completed_time,
            progress_percentage=100.0 if status == JobStatus.COMPLETED else random.uniform(0, 95) if status == JobStatus.RUNNING else 0.0,
            current_step=random.choice(["Processing", "Analyzing", "Cleaning", "Validating", "Completed"]) if status == JobStatus.RUNNING else None,
            total_steps=random.randint(3, 8),
            execution_time=random.uniform(30, 3600) if completed_time else None,
            parameters={
                "data_profile_id": random.choice(data_profiles).id if data_profiles and job_type in ["data_analysis", "data_cleaning"] else None,
                "sample_size": random.randint(1000, 10000),
                "ai_enabled": random.choice([True, False])
            },
            result={
                "status": "success" if status == JobStatus.COMPLETED else "in_progress",
                "quality_score": random.uniform(0.7, 0.95) if job_type == "data_analysis" else None,
                "records_processed": random.randint(1000, 100000) if status == JobStatus.COMPLETED else None
            } if status != JobStatus.PENDING else None,
            error_message=fake.sentence() if status == JobStatus.FAILED else None
        )
        db.add(job)
        jobs.append(job)
    
    db.commit()
    print(f"Created {len(jobs)} mock jobs")
    return jobs


def create_mock_audit_logs(db, users, count=500):
    """Create mock audit logs"""
    logs = []
    
    actions = [
        "login", "logout", "file_upload", "data_analysis_start", "migration_start",
        "connection_test", "project_create", "user_update", "password_change",
        "data_cleaning", "sql_translation", "report_generate"
    ]
    
    resource_types = ["user", "project", "data_quality", "migration", "connection", "job"]
    
    for i in range(count):
        user = random.choice(users)
        action = random.choice(actions)
        resource_type = random.choice(resource_types)
        
        log = AuditLog(
            user_id=user.id,
            action=action,
            resource_type=resource_type,
            resource_id=str(random.randint(1, 1000)),
            ip_address=fake.ipv4(),
            user_agent=fake.user_agent(),
            request_method=random.choice(["GET", "POST", "PUT", "DELETE"]),
            request_path=f"/api/{resource_type}/{action}",
            details={
                "action_details": fake.sentence(),
                "metadata": {
                    "duration_ms": random.randint(100, 5000),
                    "size_bytes": random.randint(1024, 1048576)
                }
            },
            success=random.choice([True, True, True, False]),  # 75% success rate
            error_message=fake.sentence() if random.choice([True, False, False, False]) else None,
            timestamp=datetime.utcnow() - timedelta(days=random.randint(1, 90))
        )
        db.add(log)
        logs.append(log)
    
    db.commit()
    print(f"Created {len(logs)} mock audit logs")
    return logs


def create_sample_csv_files():
    """Create sample CSV files for testing"""
    storage_dir = Path("storage/sample_data")
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    # Customer data with quality issues
    customers_data = []
    for i in range(1000):
        customers_data.append({
            "customer_id": i + 1,
            "first_name": fake.first_name() if random.random() > 0.05 else "",  # 5% missing
            "last_name": fake.last_name(),
            "email": fake.email() if random.random() > 0.08 else "",  # 8% missing
            "phone": fake.phone_number() if random.random() > 0.12 else "",  # 12% missing
            "address": fake.address().replace('\n', ', '),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "zip_code": fake.zipcode() if random.random() > 0.06 else "",  # 6% missing
            "registration_date": fake.date_between(start_date='-2y', end_date='today'),
            "is_active": random.choice([True, False]),
            "total_orders": random.randint(0, 50),
            "lifetime_value": round(random.uniform(0, 5000), 2)
        })
    
    # Add some duplicates (quality issue)
    for i in range(50):
        duplicate = customers_data[random.randint(0, 900)].copy()
        duplicate["customer_id"] = len(customers_data) + 1
        customers_data.append(duplicate)
    
    # Save customer data
    customers_df = pd.DataFrame(customers_data)
    customers_df.to_csv(storage_dir / "customers_sample.csv", index=False)
    
    # Orders data
    orders_data = []
    for i in range(5000):
        customer_id = random.randint(1, 1000)
        orders_data.append({
            "order_id": i + 1,
            "customer_id": customer_id,
            "order_date": fake.date_between(start_date='-1y', end_date='today'),
            "product_name": fake.word().title() + " " + fake.word().title(),
            "category": random.choice(["Electronics", "Clothing", "Books", "Home", "Sports"]),
            "quantity": random.randint(1, 10),
            "unit_price": round(random.uniform(10, 500), 2),
            "total_amount": 0,  # Will be calculated
            "discount": round(random.uniform(0, 50), 2) if random.random() > 0.7 else 0,
            "shipping_cost": round(random.uniform(5, 25), 2),
            "status": random.choice(["pending", "shipped", "delivered", "cancelled"]),
            "payment_method": random.choice(["credit_card", "debit_card", "paypal", "bank_transfer"])
        })
        # Calculate total amount
        orders_data[-1]["total_amount"] = round(
            (orders_data[-1]["unit_price"] * orders_data[-1]["quantity"]) - 
            orders_data[-1]["discount"] + 
            orders_data[-1]["shipping_cost"], 2
        )
    
    # Add some data quality issues
    for i in range(100):
        # Invalid dates
        orders_data[random.randint(0, 4900)]["order_date"] = "invalid_date"
    
    for i in range(150):
        # Negative prices (outliers)
        orders_data[random.randint(0, 4900)]["unit_price"] = -random.uniform(10, 100)
    
    # Save orders data
    orders_df = pd.DataFrame(orders_data)
    orders_df.to_csv(storage_dir / "orders_sample.csv", index=False)
    
    # Products data
    products_data = []
    for i in range(500):
        products_data.append({
            "product_id": i + 1,
            "product_name": fake.word().title() + " " + fake.word().title(),
            "description": fake.text(max_nb_chars=200) if random.random() > 0.1 else "",  # 10% missing
            "category": random.choice(["Electronics", "Clothing", "Books", "Home", "Sports"]),
            "brand": fake.company() if random.random() > 0.15 else "",  # 15% missing
            "price": round(random.uniform(5, 1000), 2),
            "cost": round(random.uniform(2, 500), 2),
            "stock_quantity": random.randint(0, 1000),
            "weight_kg": round(random.uniform(0.1, 50), 2) if random.random() > 0.2 else "",  # 20% missing
            "dimensions": f"{random.randint(10, 100)}x{random.randint(10, 100)}x{random.randint(5, 50)}",
            "is_active": random.choice([True, False]),
            "created_date": fake.date_between(start_date='-3y', end_date='-1y'),
            "last_updated": fake.date_between(start_date='-1y', end_date='today')
        })
    
    products_df = pd.DataFrame(products_data)
    products_df.to_csv(storage_dir / "products_sample.csv", index=False)
    
    print(f"Created sample CSV files in {storage_dir}")
    print(f"- customers_sample.csv: {len(customers_data)} records")
    print(f"- orders_sample.csv: {len(orders_data)} records")
    print(f"- products_sample.csv: {len(products_data)} records")


def main():
    """Main function to generate all mock data"""
    print("Starting mock data generation...")
    
    # Create database tables
    create_tables()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Generate all mock data
        users = create_mock_users(db, count=15)
        projects = create_mock_projects(db, users, count=25)
        connections = create_mock_connections(db, users, count=40)
        data_profiles = create_mock_data_profiles(db, projects, count=150)
        migrations = create_mock_migrations(db, projects, connections, count=60)
        jobs = create_mock_jobs(db, users, projects, data_profiles, count=300)
        audit_logs = create_mock_audit_logs(db, users, count=800)
        
        # Create sample CSV files
        create_sample_csv_files()
        
        print("\n✅ Mock data generation completed successfully!")
        print(f"Generated:")
        print(f"  - {len(users)} users")
        print(f"  - {len(projects)} projects")
        print(f"  - {len(connections)} database connections")
        print(f"  - {len(data_profiles)} data profiles")
        print(f"  - {len(migrations)} migration logs")
        print(f"  - {len(jobs)} jobs")
        print(f"  - {len(audit_logs)} audit logs")
        print(f"  - 3 sample CSV files")
        
        print("\nNote:")
        print("  All users are created with Firebase UIDs")
        print("  Use Firebase Authentication to log in with the generated emails")
        
    except Exception as e:
        print(f"❌ Error generating mock data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()