"""
AWS Cost Forecaster Lambda Function

Predicts future AWS costs using historical data and machine learning.
"""

import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from botocore.exceptions import ClientError


# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
cost_table = dynamodb.Table(os.environ.get('COST_HISTORY_TABLE', 'cost_history'))
# Forecasts stored back in cost_history with future dates
forecast_table = cost_table


def lambda_handler(event, context):
    """
    Main handler function for AWS Lambda.
    
    Generates cost forecasts based on historical data.
    
    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object
        
    Returns:
        dict: Response with status code and body
    """
    try:
        # Fetch historical cost data
        historical_data = fetch_historical_data()
        
        if historical_data is None:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Insufficient historical data'})
            }
        
        # Generate forecasts
        forecasts = generate_forecasts(historical_data)
        
        # Store forecasts
        store_forecasts(forecasts)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Forecast generated successfully',
                'forecast_days': len(forecasts)
            })
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def fetch_historical_data():
    """
    Fetch historical cost data from DynamoDB.
    
    Returns:
        pd.DataFrame: Historical cost data
    """
    try:
        # Scan table for last 90 days of data
        response = cost_table.scan()
        items = response.get('Items', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(items)
        if df.empty:
            return None
        
        # Use blueprint schema column names
        df['date'] = pd.to_datetime(df['date'])
        df['cost_usd'] = df['cost_usd'].astype(float)
        
        return df
        
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return None


def generate_forecasts(historical_data):
    """
    Generate cost forecasts using linear regression.
    
    Args:
        historical_data: Historical cost DataFrame
        
    Returns:
        list: Forecast data for next 30 days
    """
    # Aggregate daily costs using blueprint schema
    daily_costs = historical_data.groupby('date')['cost_usd'].sum().reset_index()
    daily_costs = daily_costs.sort_values('date')
    
    # Prepare data for model
    X = np.arange(len(daily_costs)).reshape(-1, 1)
    y = daily_costs['cost_usd'].values
    
    # Train simple linear regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Generate forecasts for next 30 days
    forecasts = []
    last_date = daily_costs['date'].max()
    
    for i in range(1, 31):
        forecast_date = last_date + timedelta(days=i)
        X_pred = np.array([[len(daily_costs) + i - 1]])
        predicted_cost = max(0, model.predict(X_pred)[0])  # Ensure non-negative
        
        forecasts.append({
            'date': forecast_date.strftime('%Y-%m-%d'),
            'predicted_cost': Decimal(str(round(predicted_cost, 2))),
            'confidence': 'medium',  # Placeholder for confidence interval
            'timestamp': datetime.now().isoformat()
        })
    
    return forecasts


def store_forecasts(forecasts):
    """
    Store forecast data in DynamoDB.
    
    Args:
        forecasts: List of forecast records
    """
    with forecast_table.batch_writer() as batch:
        for forecast in forecasts:
            forecast['id'] = f"forecast#{forecast['date']}"
            batch.put_item(Item=forecast)
    
    print(f"Stored {len(forecasts)} forecast records")
