"""
Tests for Notifier Lambda function.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


def test_lambda_handler_success(aws_credentials, mock_env_vars, sample_cost_data):
    """Test successful notification check."""
    with patch('notifier.lambda_notifier.cost_history_router') as mock_router:
        mock_router.query_by_date.return_value = sample_cost_data
        
        from notifier.lambda_notifier import lambda_handler
        
        response = lambda_handler({}, {})
        
        assert response['statusCode'] == 200


def test_check_cost_alerts_below_threshold(sample_cost_data):
    """Test alert checking when costs are below threshold."""
    from notifier.lambda_notifier import check_cost_alerts
    
    # Sample data totals to $41.25, below $100 threshold
    alerts = check_cost_alerts(sample_cost_data)
    
    # Should not trigger daily threshold alert
    daily_alerts = [a for a in alerts if a['type'] == 'DAILY_SPIKE']
    assert len(daily_alerts) == 0


def test_check_cost_alerts_above_threshold():
    """Test alert checking when costs exceed threshold."""
    from notifier.lambda_notifier import check_cost_alerts
    
    high_cost_data = [
        {'service_name': 'AWS Lambda', 'cost_usd': Decimal('150.00')}
    ]
    
    alerts = check_cost_alerts(high_cost_data)
    
    # Should trigger daily threshold alert
    daily_alerts = [a for a in alerts if a['type'] == 'DAILY_SPIKE']
    assert len(daily_alerts) > 0


def test_fetch_daily_costs_excludes_forecast(aws_credentials, mock_env_vars):
    """Test that forecast data is excluded from daily costs."""
    with patch('notifier.lambda_notifier.cost_history_router') as mock_router:
        mock_router.query_by_date.return_value = [
            {'service_name': 'AWS Lambda', 'cost_usd': Decimal('25.00')},
            # FORECAST should be excluded
        ]
        
        from notifier.lambda_notifier import fetch_daily_costs
        
        costs = fetch_daily_costs()
        
        # Verify exclude_forecast=True was called
        mock_router.query_by_date.assert_called_once()
        call_args = mock_router.query_by_date.call_args
        assert call_args[1]['exclude_forecast'] is True
