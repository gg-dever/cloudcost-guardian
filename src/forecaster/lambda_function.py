"""
AWS Cost Forecaster Lambda Function

Uses AWS Cost Explorer's native GetCostForecast API for predictions.
More accurate than custom ML models - uses AWS's production forecasting.
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
cost_table = dynamodb.Table(os.environ.get('COST_HISTORY_TABLE', 'cost_history'))
forecast_table = cost_table


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
            forecast_date = entry.get('TimePeriod', {}).get('Start')
            mean_value = float(entry.get('MeanValue', 0))
            
            forecasts.append({
                'date': forecast_date,
                'predicted_cost': Decimal(str(round(mean_value, 2))),
                'confidence': 'high',  # AWS's 80% prediction interval
                'source': 'aws_cost_explorer',
                'timestamp': datetime.now().isoformat()
            })
        
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
    Store forecast data in DynamoDB.
    Forecasts are stored in cost_history table with service_name='FORECAST'
    
    Args:
        forecasts: List of forecast records from AWS
    """
    try:
        with forecast_table.batch_writer() as batch:
            for forecast in forecasts:
                # cost_history table needs: date (PK) and service_name (SK)
                item = {
                    'date': forecast['date'],
                    'service_name': 'FORECAST',  # Mark as forecast data
                    'cost_usd': forecast['predicted_cost'],
                    'confidence': forecast.get('confidence', 'high'),
                    'source': forecast.get('source', 'aws_cost_explorer'),
                    'forecast_generated_at': forecast['timestamp']
                }
                batch.put_item(Item=item)
        
        print(f"Stored {len(forecasts)} forecast records in DynamoDB")
        
    except Exception as e:
        print(f"Error storing forecasts: {e}")
        raise
