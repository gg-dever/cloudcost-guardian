"""
AWS Cost Analyzer Lambda Function

Fetches and analyzes AWS cost and usage data using the Cost Explorer API.
Stores results in DynamoDB for dashboard consumption.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

# Import from Lambda Layer
from shared.schemas import CostHistoryRecord
from shared.routers.cost_history_router import cost_history_router


# Initialize AWS clients
ce_client = boto3.client('ce')  # Cost Explorer


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
    Process raw cost data from Cost Explorer API using schema mappers.
    
    Args:
        response: Response from Cost Explorer API
        
    Returns:
        list: Processed cost data records as CostHistoryRecord objects
    """
    processed_data = []
    
    for result in response.get('ResultsByTime', []):
        date = result['TimePeriod']['Start']  # PK: date (YYYY-MM-DD)
        
        for group in result.get('Groups', []):
            # Use schema mapper to parse AWS API response
            record = CostHistoryRecord.from_cost_explorer_response(group, date)
            processed_data.append(record)
    
    return processed_data


def store_in_dynamodb(cost_data):
    """
    Store cost data in DynamoDB using the cost_history_router.
    
    Args:
        cost_data: List of CostHistoryRecord objects to store
    """
    try:
        # Use router for batch storage
        stored_count = cost_history_router.put_batch(cost_data)
        
        if stored_count != len(cost_data):
            print(f"Warning: Only {stored_count}/{len(cost_data)} records stored successfully")
        
    except Exception as e:
        print(f"Error storing cost data: {e}")
        raise
    
    print(f"Stored {len(cost_data)} records in DynamoDB")
