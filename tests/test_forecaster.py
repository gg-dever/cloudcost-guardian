"""
Tests for Forecaster Lambda Function
"""

import json
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

# Import the lambda function
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/forecaster'))
from lambda_function import lambda_handler, fetch_historical_data, generate_forecasts


@pytest.fixture
def sample_historical_data():
    """Create sample historical data using blueprint schema."""
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    data = {
        'date': dates,
        'service_name': ['Amazon EC2'] * 30,  # Blueprint uses service_name
        'cost_usd': np.random.uniform(40, 60, 30)  # Blueprint uses cost_usd
    }
    return pd.DataFrame(data)


def test_generate_forecasts(sample_historical_data):
    """Test forecast generation."""
    forecasts = generate_forecasts(sample_historical_data)
    
    # Should generate 30 days of forecasts
    assert len(forecasts) == 30
    
    # Check forecast structure
    assert 'date' in forecasts[0]
    assert 'predicted_cost' in forecasts[0]
    assert 'confidence' in forecasts[0]
    
    # Costs should be non-negative
    for forecast in forecasts:
        assert float(forecast['predicted_cost']) >= 0


@patch('lambda_function.fetch_historical_data')
@patch('lambda_function.forecast_table')
def test_lambda_handler_success(mock_table, mock_fetch, sample_historical_data):
    """Test successful lambda execution."""
    # Setup mocks
    mock_fetch.return_value = sample_historical_data
    mock_table.batch_writer.return_value.__enter__.return_value = MagicMock()
    
    # Execute lambda
    response = lambda_handler({}, {})
    
    # Assertions
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['message'] == 'Forecast generated successfully'
    assert body['forecast_days'] == 30


@patch('lambda_function.fetch_historical_data')
def test_lambda_handler_insufficient_data(mock_fetch):
    """Test handling of insufficient historical data."""
    # Setup mock to return None
    mock_fetch.return_value = None
    
    # Execute lambda
    response = lambda_handler({}, {})
    
    # Assertions
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'Insufficient historical data' in body['error']


def test_forecast_trends(sample_historical_data):
    """Test that forecasts follow reasonable trends."""
    forecasts = generate_forecasts(sample_historical_data)
    
    # Extract predicted costs
    predicted_costs = [float(f['predicted_cost']) for f in forecasts]
    
    # Check that forecasts are within reasonable range using blueprint schema
    historical_mean = sample_historical_data['cost_usd'].mean()  # Blueprint uses cost_usd
    forecast_mean = np.mean(predicted_costs)
    
    # Forecast mean should be within 50% of historical mean
    assert abs(forecast_mean - historical_mean) < historical_mean * 0.5
