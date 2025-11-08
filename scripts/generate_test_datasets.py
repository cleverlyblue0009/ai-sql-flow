#!/usr/bin/env python3
"""
Generate Test Datasets for DataFlow AI Benchmarking

This script generates 5 realistic Excel datasets with deliberate data quality issues:
1. E-Commerce Customer Database (10,000 rows - reduced for faster generation)
2. Healthcare Patient Records (15,000 rows - reduced for faster generation)
3. Financial Transaction Records (20,000 rows - reduced for faster generation)
4. Sensor IoT Data (25,000 rows - reduced for faster generation)
5. Mixed Quality Dataset (5,000 rows - reduced for faster generation)

Each dataset has specific, measurable quality issues for validation.
Note: Dataset sizes have been reduced to enable faster benchmarking cycles.
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import os
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set random seed for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
Faker.seed(RANDOM_SEED)

fake = Faker()

# Output directory
OUTPUT_DIR = Path("test_data/excel")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def inject_nulls(df, column, percentage):
    """Inject NULL values into a column"""
    num_nulls = int(len(df) * percentage / 100)
    null_indices = np.random.choice(df.index, num_nulls, replace=False)
    df.loc[null_indices, column] = np.nan
    return num_nulls


def inject_exact_duplicates(df, count):
    """Inject exact duplicate rows"""
    if count > len(df):
        count = len(df) // 2
    duplicate_indices = np.random.choice(df.index, count, replace=False)
    duplicates = df.loc[duplicate_indices].copy()
    df = pd.concat([df, duplicates], ignore_index=True)
    return df, count


def inject_fuzzy_duplicates(df, columns, count):
    """Inject fuzzy duplicates with slight variations"""
    fuzzy_dups = []
    for _ in range(count):
        if len(df) == 0:
            break
        idx = np.random.choice(df.index)
        dup = df.loc[idx].copy()
        
        # Modify a random column slightly
        col = np.random.choice(columns)
        if pd.notna(dup[col]) and isinstance(dup[col], str):
            # Add typo or variation
            variations = [
                dup[col].lower(),
                dup[col].upper(),
                dup[col].replace(' ', '_'),
                dup[col].replace('.', '_'),
                dup[col] + ' ',  # trailing space
            ]
            dup[col] = np.random.choice(variations)
        
        fuzzy_dups.append(dup)
    
    if fuzzy_dups:
        fuzzy_df = pd.DataFrame(fuzzy_dups)
        df = pd.concat([df, fuzzy_df], ignore_index=True)
    
    return df, len(fuzzy_dups)


def generate_ecommerce_dataset(rows=10000):
    """Generate E-Commerce Customer Database with known quality issues"""
    logger.info(f"Generating E-Commerce dataset with {rows} rows...")
    
    data = {
        'customer_id': range(1, rows + 1),
        'email': [fake.email() for _ in range(rows)],
        'first_name': [fake.first_name() for _ in range(rows)],
        'last_name': [fake.last_name() for _ in range(rows)],
        'phone': [fake.phone_number() for _ in range(rows)],
        'address': [fake.street_address() for _ in range(rows)],
        'city': [fake.city() for _ in range(rows)],
        'state': [fake.state_abbr() for _ in range(rows)],
        'zip': [fake.zipcode() for _ in range(rows)],
        'signup_date': [fake.date_between(start_date='-5y', end_date='today') for _ in range(rows)],
        'last_purchase_date': [fake.date_between(start_date='-1y', end_date='today') for _ in range(rows)],
        'purchase_count': np.random.randint(0, 100, rows),
        'loyalty_status': np.random.choice(['Bronze', 'Silver', 'Gold', 'Platinum'], rows),
        'country': ['USA' for _ in range(rows)],
        'income_bracket': np.random.choice(['<30k', '30k-50k', '50k-75k', '75k-100k', '>100k'], rows)
    }
    
    df = pd.DataFrame(data)
    
    issues = {
        'null_values': 0,
        'exact_duplicates': 0,
        'fuzzy_duplicates': 0,
        'email_name_mismatches': 0,
        'phone_format_inconsistencies': 0,
        'invalid_emails': 0,
        'impossible_dates': 0,
        'outliers': 0,
        'invalid_zips': 0
    }
    
    # Inject 12% NULL values randomly
    for col in ['email', 'phone', 'address', 'city', 'state', 'zip']:
        nulls = inject_nulls(df, col, 2)
        issues['null_values'] += nulls
    
    # Inject exact duplicates
    df, dup_count = inject_exact_duplicates(df, 847)
    issues['exact_duplicates'] = dup_count
    
    # Inject fuzzy duplicates
    df, fuzzy_count = inject_fuzzy_duplicates(df, ['email', 'first_name', 'last_name'], 2341)
    issues['fuzzy_duplicates'] = fuzzy_count
    
    # Inject email-name mismatches (156 cases)
    mismatch_indices = np.random.choice(df.index, 156, replace=False)
    for idx in mismatch_indices:
        # Swap email with another random person
        other_idx = np.random.choice(df.index)
        df.loc[idx, 'email'] = df.loc[other_idx, 'email']
    issues['email_name_mismatches'] = 156
    
    # Phone format inconsistencies
    phone_formats = [
        lambda: f"({fake.random_int(100, 999)}) {fake.random_int(100, 999)}-{fake.random_int(1000, 9999)}",
        lambda: f"{fake.random_int(100, 999)}-{fake.random_int(100, 999)}-{fake.random_int(1000, 9999)}",
        lambda: f"{fake.random_int(100, 999)}.{fake.random_int(100, 999)}.{fake.random_int(1000, 9999)}",
        lambda: f"{fake.random_int(1000000000, 9999999999)}"
    ]
    inconsistent_indices = np.random.choice(df.index, 3421, replace=False)
    for idx in inconsistent_indices:
        df.loc[idx, 'phone'] = random.choice(phone_formats)()
    issues['phone_format_inconsistencies'] = 3421
    
    # Invalid email formats
    invalid_indices = np.random.choice(df.index, 892, replace=False)
    for idx in invalid_indices:
        corruptions = [
            lambda e: e.replace('@', ''),
            lambda e: e.replace('@', '@@'),
            lambda e: e.split('@')[0],
            lambda e: f"{e}@invalid",
        ]
        if pd.notna(df.loc[idx, 'email']):
            df.loc[idx, 'email'] = random.choice(corruptions)(str(df.loc[idx, 'email']))
    issues['invalid_emails'] = 892
    
    # Impossible dates
    date_indices = np.random.choice(df.index, 2156, replace=False)
    for idx in date_indices:
        impossible_dates = [
            datetime(1900, 1, 1),
            datetime(2030, 12, 31),  # Future date
            datetime(1899, 12, 31),
        ]
        df.loc[idx, 'signup_date'] = random.choice(impossible_dates)
    issues['impossible_dates'] = 2156
    
    # Outliers in purchase_count and income
    outlier_indices = np.random.choice(df.index, 1234, replace=False)
    for idx in outlier_indices:
        df.loc[idx, 'purchase_count'] = np.random.randint(500, 1000)  # 5-10x normal
    issues['outliers'] = 1234
    
    # Invalid zip codes
    zip_indices = np.random.choice(df.index, 445, replace=False)
    for idx in zip_indices:
        df.loc[idx, 'zip'] = 'INVALID'
    issues['invalid_zips'] = 445
    
    # Calculate expected quality metrics
    total_cells = len(df) * len(df.columns)
    null_cells = df.isnull().sum().sum()
    completeness = ((total_cells - null_cells) / total_cells) * 100
    validity = 82.0  # Estimated based on invalid emails, dates, etc.
    uniqueness = (1 - (issues['exact_duplicates'] / len(df))) * 100
    consistency = 75.0  # Estimated based on format inconsistencies
    accuracy = 85.0  # Estimated based on outliers and semantic issues
    overall = (completeness * 0.25 + validity * 0.25 + uniqueness * 0.20 + 
               consistency * 0.15 + accuracy * 0.15)
    
    metrics = {
        'completeness': completeness,
        'validity': validity,
        'uniqueness': uniqueness,
        'consistency': consistency,
        'accuracy': accuracy,
        'overall_quality_score': overall
    }
    
    return df, issues, metrics


def generate_healthcare_dataset(rows=15000):
    """Generate Healthcare Patient Records with known quality issues"""
    logger.info(f"Generating Healthcare dataset with {rows} rows...")
    
    data = {
        'patient_id': range(1, rows + 1),
        'ssn': [fake.ssn() for _ in range(rows)],
        'first_name': [fake.first_name() for _ in range(rows)],
        'last_name': [fake.last_name() for _ in range(rows)],
        'dob': [fake.date_of_birth(minimum_age=0, maximum_age=100) for _ in range(rows)],
        'gender': np.random.choice(['M', 'F'], rows),
        'email': [fake.email() for _ in range(rows)],
        'phone': [fake.phone_number() for _ in range(rows)],
        'address': [fake.street_address() for _ in range(rows)],
        'city': [fake.city() for _ in range(rows)],
        'state': [fake.state_abbr() for _ in range(rows)],
        'zip': [fake.zipcode() for _ in range(rows)],
        'insurance_provider': np.random.choice(['Aetna', 'Blue Cross', 'Cigna', 'UnitedHealth'], rows),
        'policy_number': [f"POL{fake.random_int(100000, 999999)}" for _ in range(rows)],
        'blood_type': np.random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'], rows),
        'height_cm': np.random.normal(170, 10, rows),
        'weight_kg': np.random.normal(75, 15, rows),
        'last_visit_date': [fake.date_between(start_date='-2y', end_date='today') for _ in range(rows)],
        'diagnosis_codes': [f"ICD{fake.random_int(100, 999)}" for _ in range(rows)],
        'allergies': np.random.choice(['None', 'Penicillin', 'Peanuts', 'Latex', 'Multiple'], rows),
        'medications': np.random.choice(['None', 'Aspirin', 'Insulin', 'Metformin', 'Multiple'], rows),
    }
    
    df = pd.DataFrame(data)
    
    issues = {
        'null_values': 0,
        'exact_duplicates': 0,
        'fuzzy_duplicates': 0,
        'semantic_mismatches': 0,
        'impossible_heights_weights': 0,
        'age_outliers': 0,
        'invalid_formats': 0,
        'inconsistent_gender': 0,
        'invalid_policy_numbers': 0
    }
    
    # 8% NULL values
    for col in ['email', 'phone', 'allergies', 'medications']:
        nulls = inject_nulls(df, col, 2)
        issues['null_values'] += nulls
    
    # Exact duplicates
    df, dup_count = inject_exact_duplicates(df, 1247)
    issues['exact_duplicates'] = dup_count
    
    # Fuzzy duplicates
    df, fuzzy_count = inject_fuzzy_duplicates(df, ['first_name', 'last_name', 'address'], 3892)
    issues['fuzzy_duplicates'] = fuzzy_count
    
    # Semantic mismatches (gender with name)
    mismatch_indices = np.random.choice(df.index, 892, replace=False)
    for idx in mismatch_indices:
        if df.loc[idx, 'gender'] == 'M':
            df.loc[idx, 'first_name'] = fake.first_name_female()
        else:
            df.loc[idx, 'first_name'] = fake.first_name_male()
    issues['semantic_mismatches'] = 892
    
    # Impossible heights/weights
    outlier_indices = np.random.choice(df.index, 2156, replace=False)
    for idx in outlier_indices:
        choice = np.random.choice(['height', 'weight'])
        if choice == 'height':
            df.loc[idx, 'height_cm'] = np.random.choice([-50, 350, 0])
        else:
            df.loc[idx, 'weight_kg'] = np.random.choice([-20, 500, 0])
    issues['impossible_heights_weights'] = 2156
    
    # Age outliers (impossible birth years)
    age_indices = np.random.choice(df.index, 5234, replace=False)
    for idx in age_indices:
        bad_dates = [
            datetime(1700, 1, 1),
            datetime(2030, 1, 1),
            datetime(1850, 6, 15),
        ]
        df.loc[idx, 'dob'] = random.choice(bad_dates)
    issues['age_outliers'] = 5234
    
    # Inconsistent gender representations
    gender_indices = np.random.choice(df.index, 623, replace=False)
    for idx in gender_indices:
        df.loc[idx, 'gender'] = np.random.choice(['Male', 'Female', 'm', 'f', '1', '2'])
    issues['inconsistent_gender'] = 623
    
    # Calculate expected quality metrics
    total_cells = len(df) * len(df.columns)
    null_cells = df.isnull().sum().sum()
    completeness = ((total_cells - null_cells) / total_cells) * 100
    validity = 78.0
    uniqueness = (1 - (issues['exact_duplicates'] / len(df))) * 100
    consistency = 68.0
    accuracy = 80.0
    overall = (completeness * 0.25 + validity * 0.25 + uniqueness * 0.20 + 
               consistency * 0.15 + accuracy * 0.15)
    
    metrics = {
        'completeness': completeness,
        'validity': validity,
        'uniqueness': uniqueness,
        'consistency': consistency,
        'accuracy': accuracy,
        'overall_quality_score': overall
    }
    
    return df, issues, metrics


def generate_financial_dataset(rows=20000):
    """Generate Financial Transaction Records with known quality issues"""
    logger.info(f"Generating Financial dataset with {rows} rows...")
    
    data = {
        'transaction_id': [f"TXN{i:010d}" for i in range(1, rows + 1)],
        'account_id': np.random.randint(1000, 9999, rows),
        'amount': np.random.uniform(1, 1000, rows).round(2),
        'currency': np.random.choice(['USD', 'EUR', 'GBP'], rows, p=[0.7, 0.2, 0.1]),
        'transaction_date': [fake.date_time_between(start_date='-2y', end_date='now') for _ in range(rows)],
        'merchant_name': [fake.company() for _ in range(rows)],
        'category': np.random.choice(['Groceries', 'Gas', 'Dining', 'Shopping', 'Travel'], rows),
        'payment_method': np.random.choice(['Credit Card', 'Debit Card', 'Cash', 'Check'], rows),
        'status': np.random.choice(['completed', 'pending', 'failed'], rows, p=[0.85, 0.10, 0.05]),
        'fraud_flag': np.random.choice([0, 1], rows, p=[0.98, 0.02]),
        'settlement_date': [fake.date_time_between(start_date='-2y', end_date='now') for _ in range(rows)],
        'description': [fake.sentence() for _ in range(rows)],
    }
    
    df = pd.DataFrame(data)
    
    issues = {
        'null_values': 0,
        'exact_duplicates': 0,
        'fuzzy_duplicates': 0,
        'amount_outliers': 0,
        'impossible_dates': 0,
        'invalid_currencies': 0,
        'inconsistent_merchants': 0,
        'invalid_categories': 0,
        'inconsistent_status': 0,
        'fraud_anomalies': 0
    }
    
    # 2% NULL values
    nulls = inject_nulls(df, 'description', 2)
    issues['null_values'] = nulls
    
    # Exact duplicates
    df, dup_count = inject_exact_duplicates(df, 234)
    issues['exact_duplicates'] = dup_count
    
    # Fuzzy duplicates
    df, fuzzy_count = inject_fuzzy_duplicates(df, ['merchant_name'], 4567)
    issues['fuzzy_duplicates'] = fuzzy_count
    
    # Amount outliers
    outlier_indices = np.random.choice(df.index, 12345, replace=False)
    for idx in outlier_indices:
        df.loc[idx, 'amount'] = np.random.choice([0.01, 99999.99, -100])
    issues['amount_outliers'] = 12345
    
    # Impossible dates (settlement before transaction)
    date_indices = np.random.choice(df.index, 2234, replace=False)
    for idx in date_indices:
        df.loc[idx, 'settlement_date'] = df.loc[idx, 'transaction_date'] - timedelta(days=np.random.randint(1, 30))
    issues['impossible_dates'] = 2234
    
    # Invalid currency codes
    currency_indices = np.random.choice(df.index, 5678, replace=False)
    for idx in currency_indices:
        df.loc[idx, 'currency'] = np.random.choice(['XXX', 'INVALID', '123', 'US'])
    issues['invalid_currencies'] = 5678
    
    # Inconsistent merchant names (Starbucks/STARBUCKS/starbucks)
    merchant_indices = np.random.choice(df.index, 3456, replace=False)
    for idx in merchant_indices:
        variations = ['Starbucks', 'STARBUCKS', 'starbucks', 'Starbucks Coffee', 'Starbucks Corp']
        df.loc[idx, 'merchant_name'] = np.random.choice(variations)
    issues['inconsistent_merchants'] = 3456
    
    # Inconsistent status values
    status_indices = np.random.choice(df.index, 892, replace=False)
    for idx in status_indices:
        df.loc[idx, 'status'] = np.random.choice(['Completed', 'COMPLETE', 'comp', 'done'])
    issues['inconsistent_status'] = 892
    
    # Calculate metrics
    total_cells = len(df) * len(df.columns)
    null_cells = df.isnull().sum().sum()
    completeness = ((total_cells - null_cells) / total_cells) * 100
    validity = 85.0
    uniqueness = (1 - (issues['exact_duplicates'] / len(df))) * 100
    consistency = 72.0
    accuracy = 88.0
    overall = (completeness * 0.25 + validity * 0.25 + uniqueness * 0.20 + 
               consistency * 0.15 + accuracy * 0.15)
    
    metrics = {
        'completeness': completeness,
        'validity': validity,
        'uniqueness': uniqueness,
        'consistency': consistency,
        'accuracy': accuracy,
        'overall_quality_score': overall
    }
    
    return df, issues, metrics


def generate_iot_dataset(rows=25000):
    """Generate Sensor IoT Data with known quality issues"""
    logger.info(f"Generating IoT dataset with {rows} rows...")
    
    data = {
        'sensor_id': [f"SENSOR{np.random.randint(1, 1000):04d}" for _ in range(rows)],
        'timestamp': [fake.date_time_between(start_date='-30d', end_date='now') for _ in range(rows)],
        'temperature_celsius': np.random.normal(20, 5, rows),
        'humidity_percent': np.random.uniform(30, 70, rows),
        'pressure_mb': np.random.normal(1013, 10, rows),
        'air_quality_index': np.random.randint(0, 200, rows),
        'location': [f"Zone-{np.random.choice(['A', 'B', 'C', 'D'])}" for _ in range(rows)],
        'device_status': np.random.choice(['on', 'off', 'maintenance'], rows, p=[0.85, 0.10, 0.05]),
        'battery_level': np.random.uniform(0, 100, rows),
        'signal_strength': np.random.uniform(-90, -30, rows),
    }
    
    df = pd.DataFrame(data)
    
    issues = {
        'null_values': 0,
        'exact_duplicates': 0,
        'temperature_outliers': 0,
        'humidity_outliers': 0,
        'pressure_outliers': 0,
        'timestamp_issues': 0,
        'inconsistent_sensor_ids': 0,
        'inconsistent_status': 0,
        'battery_outliers': 0,
        'signal_outliers': 0
    }
    
    # 5% NULL values (sensor failures)
    for col in ['temperature_celsius', 'humidity_percent', 'pressure_mb']:
        nulls = inject_nulls(df, col, 1.67)
        issues['null_values'] += nulls
    
    # Exact duplicates
    df, dup_count = inject_exact_duplicates(df, 892)
    issues['exact_duplicates'] = dup_count
    
    # Temperature outliers
    temp_indices = np.random.choice(df.index, 3456, replace=False)
    for idx in temp_indices:
        df.loc[idx, 'temperature_celsius'] = np.random.choice([-273, 150, -100, 200])
    issues['temperature_outliers'] = 3456
    
    # Humidity outliers
    humid_indices = np.random.choice(df.index, 2341, replace=False)
    for idx in humid_indices:
        df.loc[idx, 'humidity_percent'] = np.random.choice([-10, 150, 200])
    issues['humidity_outliers'] = 2341
    
    # Pressure outliers
    pressure_indices = np.random.choice(df.index, 4567, replace=False)
    for idx in pressure_indices:
        df.loc[idx, 'pressure_mb'] = np.random.choice([0, 2000, -500])
    issues['pressure_outliers'] = 4567
    
    # Inconsistent status
    status_indices = np.random.choice(df.index, 1234, replace=False)
    for idx in status_indices:
        df.loc[idx, 'device_status'] = np.random.choice(['ON', '1', 'true', 'active'])
    issues['inconsistent_status'] = 1234
    
    # Battery percentage >100%
    battery_indices = np.random.choice(df.index, 678, replace=False)
    for idx in battery_indices:
        df.loc[idx, 'battery_level'] = np.random.uniform(100, 200)
    issues['battery_outliers'] = 678
    
    # Calculate metrics
    total_cells = len(df) * len(df.columns)
    null_cells = df.isnull().sum().sum()
    completeness = ((total_cells - null_cells) / total_cells) * 100
    validity = 81.0
    uniqueness = (1 - (issues['exact_duplicates'] / len(df))) * 100
    consistency = 83.0
    accuracy = 75.0
    overall = (completeness * 0.25 + validity * 0.25 + uniqueness * 0.20 + 
               consistency * 0.15 + accuracy * 0.15)
    
    metrics = {
        'completeness': completeness,
        'validity': validity,
        'uniqueness': uniqueness,
        'consistency': consistency,
        'accuracy': accuracy,
        'overall_quality_score': overall
    }
    
    return df, issues, metrics


def generate_mixed_dataset(rows=5000):
    """Generate Mixed Quality Dataset for quick testing"""
    logger.info(f"Generating Mixed Quality dataset with {rows} rows...")
    
    data = {
        'id': range(1, rows + 1),
        'name': [fake.name() for _ in range(rows)],
        'email': [fake.email() for _ in range(rows)],
        'phone': [fake.phone_number() for _ in range(rows)],
        'age': np.random.randint(18, 80, rows),
        'salary': np.random.uniform(30000, 120000, rows).round(2),
        'hire_date': [fake.date_between(start_date='-10y', end_date='today') for _ in range(rows)],
        'status': np.random.choice(['Active', 'Inactive', 'On Leave'], rows),
    }
    
    df = pd.DataFrame(data)
    
    issues = {
        'null_values': 0,
        'exact_duplicates': 0,
        'fuzzy_duplicates': 0,
        'outliers': 0,
        'format_inconsistencies': 0,
        'semantic_mismatches': 0
    }
    
    # 15% NULL values
    for col in ['email', 'phone', 'hire_date']:
        nulls = inject_nulls(df, col, 5)
        issues['null_values'] += nulls
    
    # Duplicates
    df, dup_count = inject_exact_duplicates(df, 567)
    issues['exact_duplicates'] = dup_count
    
    df, fuzzy_count = inject_fuzzy_duplicates(df, ['name', 'email'], 234)
    issues['fuzzy_duplicates'] = fuzzy_count
    
    # Outliers
    outlier_indices = np.random.choice(df.index, 892, replace=False)
    for idx in outlier_indices:
        df.loc[idx, 'salary'] = np.random.uniform(500000, 1000000)
        df.loc[idx, 'age'] = np.random.choice([15, 120, 150])
    issues['outliers'] = 892
    
    # Format inconsistencies
    format_indices = np.random.choice(df.index, 1500, replace=False)
    for idx in format_indices:
        df.loc[idx, 'status'] = np.random.choice(['ACTIVE', 'active', 'Act', 'A'])
    issues['format_inconsistencies'] = 1500
    
    # Calculate metrics
    total_cells = len(df) * len(df.columns)
    null_cells = df.isnull().sum().sum()
    completeness = ((total_cells - null_cells) / total_cells) * 100
    validity = 70.0
    uniqueness = (1 - (issues['exact_duplicates'] / len(df))) * 100
    consistency = 65.0
    accuracy = 72.0
    overall = (completeness * 0.25 + validity * 0.25 + uniqueness * 0.20 + 
               consistency * 0.15 + accuracy * 0.15)
    
    metrics = {
        'completeness': completeness,
        'validity': validity,
        'uniqueness': uniqueness,
        'consistency': consistency,
        'accuracy': accuracy,
        'overall_quality_score': overall
    }
    
    return df, issues, metrics


def save_dataset(df, name, issues, metrics):
    """Save dataset to Excel and metadata to JSON"""
    filename = OUTPUT_DIR / f"{name}.xlsx"
    metadata_file = OUTPUT_DIR / f"{name}_metadata.json"
    
    logger.info(f"Saving {name} to {filename}...")
    
    # Save to Excel
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    
    # Save metadata
    metadata = {
        'name': name,
        'rows': len(df),
        'columns': len(df.columns),
        'size_mb': os.path.getsize(filename) / (1024 * 1024),
        'generated_at': datetime.now().isoformat(),
        'random_seed': RANDOM_SEED,
        'injected_issues': issues,
        'expected_quality_metrics': metrics
    }
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"  - Rows: {len(df):,}")
    logger.info(f"  - Columns: {len(df.columns)}")
    logger.info(f"  - Size: {metadata['size_mb']:.2f} MB")
    logger.info(f"  - Overall Quality Score: {metrics['overall_quality_score']:.2f}%")
    
    return filename, metadata


def generate_all_datasets():
    """Generate all test datasets"""
    logger.info("=" * 80)
    logger.info("DataFlow AI: Test Dataset Generation")
    logger.info("=" * 80)
    logger.info("Note: Dataset sizes have been optimized for faster generation")
    logger.info("Total rows to generate: 75,000 (reduced from 3.9M)")
    logger.info("=" * 80)
    
    datasets = []
    
    # Dataset 1: E-Commerce (10K rows)
    logger.info("\n[1/5] Generating E-Commerce dataset...")
    df1, issues1, metrics1 = generate_ecommerce_dataset(10000)
    file1, meta1 = save_dataset(df1, 'ecommerce_customers_10k', issues1, metrics1)
    datasets.append(meta1)
    
    # Dataset 2: Healthcare (15K rows)
    logger.info("\n[2/5] Generating Healthcare dataset...")
    df2, issues2, metrics2 = generate_healthcare_dataset(15000)
    file2, meta2 = save_dataset(df2, 'healthcare_patients_15k', issues2, metrics2)
    datasets.append(meta2)
    
    # Dataset 3: Financial (20K rows)
    logger.info("\n[3/5] Generating Financial dataset...")
    df3, issues3, metrics3 = generate_financial_dataset(20000)
    file3, meta3 = save_dataset(df3, 'financial_transactions_20k', issues3, metrics3)
    datasets.append(meta3)
    
    # Dataset 4: IoT (25K rows)
    logger.info("\n[4/5] Generating IoT dataset...")
    df4, issues4, metrics4 = generate_iot_dataset(25000)
    file4, meta4 = save_dataset(df4, 'iot_sensor_data_25k', issues4, metrics4)
    datasets.append(meta4)
    
    # Dataset 5: Mixed Quality (5K rows)
    logger.info("\n[5/5] Generating Mixed Quality dataset...")
    df5, issues5, metrics5 = generate_mixed_dataset(5000)
    file5, meta5 = save_dataset(df5, 'mixed_quality_5k', issues5, metrics5)
    datasets.append(meta5)
    
    # Save summary
    summary_file = OUTPUT_DIR / 'datasets_summary.json'
    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_datasets': len(datasets),
        'total_rows': sum(d['rows'] for d in datasets),
        'total_size_mb': sum(d['size_mb'] for d in datasets),
        'datasets': datasets
    }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("=" * 80)
    logger.info("Generation Complete!")
    logger.info(f"Total Datasets: {len(datasets)}")
    logger.info(f"Total Rows: {summary['total_rows']:,}")
    logger.info(f"Total Size: {summary['total_size_mb']:.2f} MB")
    logger.info(f"Output Directory: {OUTPUT_DIR.absolute()}")
    logger.info("=" * 80)


if __name__ == "__main__":
    generate_all_datasets()
