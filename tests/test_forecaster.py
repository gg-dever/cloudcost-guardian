"""
Tests for Forecaster Lambda function.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


def test_lambda_handler_success(aws_credentials, mock_env_vars, sample_forecast_response):
    """Test successful forecast generation."""
    with patch('boto3.client') as mock_boto3:
        mock_ce = MagicMock()
        mock_ce.get_cost_forecast.return_value = sample_forecast_response
        mock_boto3.return_value = mock_ce
        
        from forecaster.lambda_forecaster import lambda_handler
        
        response = lambda_handler({}, {})
        
        assert response['statusCode'] == 200
        assert 'forecast_days' in response['body']


def test_fetch_aws_forecast(aws_credentials, sample_forecast_response):
    """Test AWS forecast fetching."""
    with patch('boto3.client') as mock_boto3:
        mock_ce = MagicMock()
        mock_ce.get_cost_forecast.return_value = sample_forecast_response
        mock_boto3.return_value = mock_ce
        
        from forecaster.lambda_forecaster import fetch_aws_forecast
        
        forecasts = fetch_aws_forecast()
        
        assert len(forecasts) > 0
        assert forecasts[0].service_name == 'FORECAST'


def test_lambda_handler_no_data(aws_credentials, mock_env_vars):
    """Test handling of empty forecast response."""
    with patch('boto3.client') as mock_boto3:
        mock_ce = MagicMock()
        mock_ce.get_cost_forecast.return_value = {'ForecastResultsByTime': []}
        mock_boto3.return_value = mock_ce
        
        from forecaster.lambda_forecaster import lambda_handler
        
        response = lambda_handler({}, {})
        
        assert response['statusCode'] == 200
