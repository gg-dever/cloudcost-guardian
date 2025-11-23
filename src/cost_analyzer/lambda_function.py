"""
AWS Cost Analyzer Lambda Function

Fetches and analyzes AWS cost and usage data using the Cost Explorer API.
Stores results in DynamoDB for dashboard consumption.
"""

import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError


# Initialize AWS clients
ce_client = boto3.client('ce')  # Cost Explorer
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('COST_HISTORY_TABLE', 'cost_history'))


def lambda_handler(event, context):
    """
    Main handler function for AWS Lambda.
    
    Fetches cost data from AWS Cost Explorer and stores it in DynamoDB.
    
    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object
        
    Returns:
        dict: Response with status code and body
    """
    try:
        # Define time range (last 30 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        # Fetch cost and usage data
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost', 'UsageQuantity'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}
            ]
        )
        
        # Process and store results
        cost_data = process_cost_data(response)
        store_in_dynamodb(cost_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Cost analysis completed successfully',
                'records_processed': len(cost_data)
            })
        }
        
    except ClientError as e:
        print(f"AWS Client Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def process_cost_data(response):
    """
    Process raw cost data from Cost Explorer API.
    
    Args:
        response: Response from Cost Explorer API
        
    Returns:
        list: Processed cost data records
    """
    processed_data = []
    
    for result in response.get('ResultsByTime', []):
        date = result['TimePeriod']['Start']  # PK: date (YYYY-MM-DD)
        
        for group in result.get('Groups', []):
            service_name = group['Keys'][0]  # SK: service_name
            cost_usd = float(group['Metrics']['UnblendedCost']['Amount'])
            usage_quantity = float(group['Metrics'].get('UsageQuantity', {}).get('Amount', 0))
            
            # Calculate TTL (90 days from now)
            ttl = int((datetime.now() + timedelta(days=90)).timestamp())
            
            processed_data.append({
                'date': date,  # Partition Key
                'service_name': service_name,  # Sort Key
                'cost_usd': Decimal(str(cost_usd)),
                'usage_quantity': Decimal(str(usage_quantity)),
                'usage_unit': 'Units',  # Default unit
                'created_at': datetime.now().isoformat(),
                'ttl': ttl  # Auto-delete after 90 days
            })
    
    return processed_data


def store_in_dynamodb(cost_data):
    """
    Store processed cost data in DynamoDB.
    
    Args:
        cost_data: List of cost data records to store
    """
    with table.batch_writer() as batch:
        for item in cost_data:
            # No composite key needed - PK (date) and SK (service_name) define uniqueness
            batch.put_item(Item=item)
    
    print(f"Stored {len(cost_data)} records in DynamoDB")
