"""
AWS Cost Forecaster Lambda Function

Uses AWS Cost Explorer's native GetCostForecast API for predictions.
More accurate than custom ML models - uses AWS's production forecasting.
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
    
    Uses AWS Cost Explorer's native GetCostForecast API.
    
    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object
        
    Returns:
        dict: Response with status code and body
    """
    try:
        print("Fetching cost forecasts from AWS Cost Explorer API...")
        
        # Get forecasts from AWS
        forecast_data = fetch_aws_forecast()
        
        if not forecast_data:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No forecast data available'})
            }
        
        print(f"Received {len(forecast_data)} days of forecast data")
        
        # Store forecasts in DynamoDB
        store_forecasts(forecast_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Forecast generated successfully',
                'forecast_days': len(forecast_data)
            })
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def fetch_aws_forecast():
    """
    Fetch cost forecasts using AWS Cost Explorer's native API.
    Uses GetCostForecast which provides AWS's production-grade predictions.
    
    Returns:
        list: Forecast data for next 30 days
    """
    try:
        # Define time period for forecast
        today = datetime.now().date()
        start_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')  # Tomorrow
        end_date = (today + timedelta(days=31)).strftime('%Y-%m-%d')    # 30 days out
        
        # Call AWS Cost Explorer forecast API
        response = ce_client.get_cost_forecast(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Metric='UNBLENDED_COST',  # Standard cost metric
            Granularity='DAILY',
            PredictionIntervalLevel=80  # 80% confidence interval
        )
        
        # Parse forecast results
        forecasts = []
        total_amount = response.get('Total', {}).get('Amount', '0')
        
        print(f"Total forecast for period: ${total_amount}")
        
        # AWS returns time series data
        time_series = response.get('ForecastResultsByTime', [])
        
        for entry in time_series:
            # Use schema mapper to parse AWS forecast response
            record = CostHistoryRecord.from_forecast_response(entry)
            forecasts.append(record)
        
        return forecasts
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'DataUnavailableException':
            print("Not enough historical data for forecast (need at least 3 months)")
        else:
            print(f"AWS API error: {e}")
        return []
    except Exception as e:
        print(f"Error fetching AWS forecast: {e}")
        return []


def store_forecasts(forecasts):
    """
    Store forecast data in DynamoDB using the cost_history_router.
    Forecasts are stored in cost_history table with service_name='FORECAST'
    
    Args:
        forecasts: List of CostHistoryRecord objects from AWS forecast
    """
    try:
        # Use router for batch storage
        stored_count = cost_history_router.put_batch(forecasts)
        
        if stored_count != len(forecasts):
            print(f"Warning: Only {stored_count}/{len(forecasts)} forecast records stored successfully")
        
    except Exception as e:
        print(f"Error storing forecasts: {e}")
        raise
