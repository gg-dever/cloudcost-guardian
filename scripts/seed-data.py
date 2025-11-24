"""
Seed Data Generator for CloudCost Guardian

Generates sample cost data for testing and development.
"""

import json
import random
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError


# AWS Services to simulate
AWS_SERVICES = [
    'Amazon Elastic Compute Cloud - Compute',
    'Amazon Simple Storage Service',
    'Amazon Relational Database Service',
    'AWS Lambda',
    'Amazon CloudFront',
    'Amazon DynamoDB',
    'Amazon SNS',
    'AWS Data Transfer'
]

# DynamoDB configuration (using blueprint table names)
COST_HISTORY_TABLE = 'cost_history'
ANOMALIES_TABLE = 'cost_anomalies'
RECOMMENDATIONS_TABLE = 'cost_recommendations'
REGION = 'us-east-1'


def generate_cost_data(days=90):
    """
    Generate sample cost data for the specified number of days.
    
    Args:
        days: Number of days of data to generate
        
    Returns:
        list: Sample cost records
    """
    records = []
    end_date = datetime.now().date()
    
    for day_offset in range(days):
        date = end_date - timedelta(days=day_offset)
        date_str = date.strftime('%Y-%m-%d')
        
        # Generate costs for each service
        for service in AWS_SERVICES:
            # Generate realistic-looking costs with some variation
            base_cost = random.uniform(10, 200)
            
            # Add some trend (increasing over time)
            trend_factor = 1 + (day_offset / days) * 0.2
            cost = base_cost / trend_factor
            
            # Add some randomness
            cost *= random.uniform(0.8, 1.2)
            
            # Calculate TTL (90 days from now)
            ttl = int((datetime.now() + timedelta(days=90)).timestamp())
            
            # Blueprint schema for cost_history table
            record = {
                'date': date_str,  # Partition Key
                'service_name': service,  # Sort Key
                'cost_usd': round(cost, 2),
                'usage_quantity': round(random.uniform(100, 10000), 2),
                'usage_unit': 'Units',
                'usage_type': 'Standard',
                'created_at': datetime.now().isoformat(),
                'ttl': ttl
            }
            
            records.append(record)
    
    return records


def save_to_dynamodb(records, table_name):
    """
    Save generated records to DynamoDB.
    
    Args:
        records: List of records to save
        table_name: Name of the DynamoDB table
    """
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(table_name)
        
        print(f"Saving {len(records)} records to DynamoDB table '{table_name}'...")
        
        with table.batch_writer() as batch:
            for record in records:
                # Convert float to Decimal for DynamoDB (blueprint uses cost_usd)
                record['cost_usd'] = Decimal(str(record['cost_usd']))
                record['usage_quantity'] = Decimal(str(record['usage_quantity']))
                batch.put_item(Item=record)
        
        print(f"✓ Successfully saved {len(records)} records")
        
    except ClientError as e:
        print(f"Error saving to DynamoDB: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def generate_anomalies_data(days=30):
    """
    Generate sample cost anomaly data.
    
    Args:
        days: Number of days of anomalies to generate
        
    Returns:
        list: Sample anomaly records
    """
    import uuid
    anomalies = []
    end_date = datetime.now().date()
    
    anomaly_types = ['SERVICE_SPIKE', 'DAILY_SPIKE', 'BUDGET_RISK']
    severities = ['HIGH', 'MEDIUM', 'LOW']
    
    # Generate 1-2 anomalies per week
    num_anomalies = days // 7 * 2
    
    for i in range(num_anomalies):
        date = end_date - timedelta(days=random.randint(0, days))
        date_str = date.strftime('%Y-%m-%d')
        
        anomaly_type = random.choice(anomaly_types)
        service = random.choice(AWS_SERVICES)
        
        actual_cost = random.uniform(100, 500)
        expected_cost = actual_cost / random.uniform(1.5, 3.5)
        percent_increase = ((actual_cost - expected_cost) / expected_cost) * 100
        
        # Determine severity based on percent increase
        if percent_increase > 50:
            severity = 'HIGH'
        elif percent_increase > 20:
            severity = 'MEDIUM'
        else:
            severity = 'LOW'
        
        # Calculate TTL (90 days from now)
        ttl = int((datetime.now() + timedelta(days=90)).timestamp())
        
        anomaly = {
            'anomaly_type': anomaly_type,  # Partition Key
            'detection_date': date_str,     # Sort Key
            'anomaly_id': str(uuid.uuid4()),
            'service_name': service,
            'actual_cost': round(actual_cost, 2),
            'expected_cost': round(expected_cost, 2),
            'percent_increase': round(percent_increase, 2),
            'severity': severity,
            'details': f"{service} costs increased {percent_increase:.1f}% from ${expected_cost:.2f} to ${actual_cost:.2f}",
            'resolution_status': random.choice(['NEW', 'ACKNOWLEDGED', 'RESOLVED']),
            'created_at': datetime.now().isoformat(),
            'ttl': ttl
        }
        
        anomalies.append(anomaly)
    
    return anomalies


def generate_recommendations_data(count=25):
    """
    Generate sample cost recommendation data.
    
    Args:
        count: Number of recommendations to generate
        
    Returns:
        list: Sample recommendation records
    """
    import uuid
    recommendations = []
    end_date = datetime.now().date()
    
    rec_types = ['RIGHT_SIZE', 'UNUSED_RESOURCE', 'SAVINGS_PLAN', 'RESERVED_INSTANCE']
    priorities = ['HIGH', 'MEDIUM', 'LOW']
    confidences = ['HIGH', 'MEDIUM', 'LOW']
    efforts = ['LOW', 'MEDIUM', 'HIGH']
    statuses = ['NEW', 'IN_PROGRESS', 'IMPLEMENTED', 'REJECTED']
    
    for i in range(count):
        date = end_date - timedelta(days=random.randint(0, 30))
        date_str = date.strftime('%Y-%m-%d')
        
        rec_type = random.choice(rec_types)
        service = random.choice(AWS_SERVICES)
        
        current_cost = random.uniform(25, 500)
        savings_percent = random.uniform(15, 60)
        potential_savings = current_cost * (savings_percent / 100)
        
        # Priority based on savings amount
        if potential_savings > 100:
            priority = 'HIGH'
        elif potential_savings > 25:
            priority = 'MEDIUM'
        else:
            priority = 'LOW'
        
        # Calculate TTL (180 days from now for recommendations)
        ttl = int((datetime.now() + timedelta(days=180)).timestamp())
        
        recommendation = {
            'recommendation_type': rec_type,  # Partition Key
            'generated_date': date_str,        # Sort Key
            'recommendation_id': str(uuid.uuid4()),
            'resource_id': f"i-{uuid.uuid4().hex[:16]}",
            'service_name': service,
            'current_cost': round(current_cost, 2),
            'potential_savings': round(potential_savings, 2),
            'savings_percent': round(savings_percent, 1),
            'recommendation': f"{rec_type.replace('_', ' ').title()} opportunity for {service}",
            'priority': priority,
            'confidence': random.choice(confidences),
            'implementation_effort': random.choice(efforts),
            'status': random.choice(statuses),
            'details': {
                'reasoning': f'Detected optimization opportunity based on usage patterns',
                'impact': f'${potential_savings:.2f}/month savings'
            },
            'created_at': datetime.now().isoformat(),
            'ttl': ttl
        }
        
        recommendations.append(recommendation)
    
    return recommendations


def save_to_json(records, filename='seed-data.json'):
    """
    Save generated records to a JSON file.
    
    Args:
        records: List of cost records to save
        filename: Output filename
    """
    try:
        with open(filename, 'w') as f:
            json.dump(records, f, indent=2)
        
        print(f"✓ Saved {len(records)} records to {filename}")
        
    except Exception as e:
        print(f"Error saving to JSON: {e}")


def main():
    """Main execution function."""
    print("CloudCost Guardian - Seed Data Generator")
    print("=========================================\n")
    
    # Generate all data
    print("Generating sample data...")
    cost_records = generate_cost_data(days=90)
    print(f"✓ Generated {len(cost_records)} cost history records (90 days)")
    
    anomalies = generate_anomalies_data(days=30)
    print(f"✓ Generated {len(anomalies)} anomaly records (30 days)")
    
    recommendations = generate_recommendations_data(count=25)
    print(f"✓ Generated {len(recommendations)} recommendation records\n")
    
    # Save to JSON for dashboard
    save_to_json(cost_records, 'src/dashboard/data/sample-data.json')
    print()
    
    # Ask if user wants to save to DynamoDB
    response = input("Do you want to save data to DynamoDB? (y/n): ")
    if response.lower() == 'y':
        print()
        save_to_dynamodb(cost_records, COST_HISTORY_TABLE)
        print(f"✅ Seeded {len(cost_records)} records to cost_history\n")
        
        save_to_dynamodb(anomalies, ANOMALIES_TABLE)
        print(f"✅ Seeded {len(anomalies)} records to cost_anomalies\n")
        
        save_to_dynamodb(recommendations, RECOMMENDATIONS_TABLE)
        print(f"✅ Seeded {len(recommendations)} records to cost_recommendations\n")
    else:
        print("Skipping DynamoDB save")
    
    print("\nDone!")


if __name__ == '__main__':
    main()
