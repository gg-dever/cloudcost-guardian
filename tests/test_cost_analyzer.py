"""
Tests for Cost Analyzer Lambda function.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


def test_lambda_handler_success(aws_credentials, mock_env_vars, sample_cost_explorer_response):
    """Test successful cost analysis execution."""
    with patch('boto3.client') as mock_boto3:
        # Mock Cost Explorer client
        mock_ce = MagicMock()
        mock_ce.get_cost_and_usage.return_value = sample_cost_explorer_response
        mock_boto3.return_value = mock_ce
        
        # Import after mocking
        from cost_analyzer.lambda_cost_analyzer import lambda_handler
        
        response = lambda_handler({}, {})
        
        assert response['statusCode'] == 200
        assert 'records_processed' in response['body']


def test_process_cost_data(sample_cost_explorer_response):
    """Test cost data processing."""
    from cost_analyzer.lambda_cost_analyzer import process_cost_data
    
    processed = process_cost_data(sample_cost_explorer_response)
    
    assert len(processed) == 2
    assert processed[0].service_name == 'AWS Lambda'
    assert processed[0].cost_usd == Decimal('25.50')


def test_lambda_handler_with_empty_response(aws_credentials, mock_env_vars):
    """Test handling of empty Cost Explorer response."""
    with patch('boto3.client') as mock_boto3:
        mock_ce = MagicMock()
        mock_ce.get_cost_and_usage.return_value = {'ResultsByTime': []}
        mock_boto3.return_value = mock_ce
        
        from cost_analyzer.lambda_cost_analyzer import lambda_handler
        
        response = lambda_handler({}, {})
        
        assert response['statusCode'] == 200
