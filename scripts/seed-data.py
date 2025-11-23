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

# DynamoDB configuration (using blueprint table name)
DYNAMODB_TABLE = 'cost_history'
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


def save_to_dynamodb(records):
    """
    Save generated records to DynamoDB.
    
    Args:
        records: List of cost records to save
    """
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(DYNAMODB_TABLE)
        
        print(f"Saving {len(records)} records to DynamoDB table '{DYNAMODB_TABLE}'...")
        
        with table.batch_writer() as batch:
            for record in records:
                # Convert float to Decimal for DynamoDB
                record['cost'] = Decimal(str(record['cost']))
                batch.put_item(Item=record)
        
        print(f"✓ Successfully saved {len(records)} records")
        
    except ClientError as e:
        print(f"Error saving to DynamoDB: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


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
    
    # Generate data
    print("Generating sample cost data...")
    records = generate_cost_data(days=90)
    print(f"✓ Generated {len(records)} records for 90 days\n")
    
    # Save to JSON
    save_to_json(records, 'src/dashboard/data/sample-data.json')
    print()
    
    # Ask if user wants to save to DynamoDB
    response = input("Do you want to save data to DynamoDB? (y/n): ")
    if response.lower() == 'y':
        save_to_dynamodb(records)
    else:
        print("Skipping DynamoDB save")
    
    print("\nDone!")


if __name__ == '__main__':
    main()
