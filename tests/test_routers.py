"""
Tests for DynamoDB routers.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime


def test_cost_history_router_query_by_date(aws_credentials):
    """Test querying cost history by date."""
    with patch('boto3.resource') as mock_boto3:
        mock_table = MagicMock()
        mock_table.query.return_value = {
            'Items': [
                {'date': '2025-11-26', 'service_name': 'AWS Lambda', 'cost_usd': Decimal('25.50')}
            ]
        }
        mock_boto3.return_value.Table.return_value = mock_table
        
        from shared.routers.cost_history_router import CostHistoryRouter
        
        router = CostHistoryRouter()
        results = router.query_by_date('2025-11-26', exclude_forecast=True)
        
        assert len(results) == 1
        assert results[0]['service_name'] == 'AWS Lambda'


def test_cost_anomalies_router_create_anomaly(aws_credentials):
    """Test creating an anomaly record."""
    with patch('boto3.resource') as mock_boto3:
        mock_table = MagicMock()
        mock_boto3.return_value.Table.return_value = mock_table
        
        from shared.routers.cost_anomalies_router import CostAnomaliesRouter
        
        router = CostAnomaliesRouter()
        anomaly = router.create_anomaly(
            anomaly_type='SERVICE_SPIKE',
            severity='HIGH',
            message='Test anomaly',
            service_name='AWS Lambda',
            cost_usd=Decimal('150.00')
        )
        
        assert anomaly is not None
        assert anomaly['anomaly_type'] == 'SERVICE_SPIKE'


def test_cost_recommendations_router_create_recommendation(aws_credentials):
    """Test creating a recommendation record."""
    with patch('boto3.resource') as mock_boto3:
        mock_table = MagicMock()
        mock_boto3.return_value.Table.return_value = mock_table
        
        from shared.routers.cost_recommendations_router import CostRecommendationsRouter
        
        router = CostRecommendationsRouter()
        rec = router.create_recommendation(
            recommendation_type='RIGHT_SIZE',
            service_name='AWS Lambda',
            recommendation='Test recommendation',
            current_cost=Decimal('100.00'),
            potential_savings=Decimal('25.00'),
            priority='high'
        )
        
        assert rec is not None
        assert rec['recommendation_type'] == 'RIGHT_SIZE'
        assert rec['savings_percent'] == Decimal('25.0')


def test_cost_history_router_excludes_forecast():
    """Test that FORECAST data can be excluded."""
    with patch('boto3.resource') as mock_boto3:
        mock_table = MagicMock()
        mock_table.query.return_value = {
            'Items': [
                {'date': '2025-11-26', 'service_name': 'AWS Lambda', 'cost_usd': Decimal('25.50')},
                {'date': '2025-11-26', 'service_name': 'FORECAST', 'cost_usd': Decimal('0.79')}
            ]
        }
        mock_boto3.return_value.Table.return_value = mock_table
        
        from shared.routers.cost_history_router import CostHistoryRouter
        
        router = CostHistoryRouter()
        results = router.query_by_date('2025-11-26', exclude_forecast=True)
        
        # FORECAST should be filtered out
        assert len(results) == 1
        assert results[0]['service_name'] == 'AWS Lambda'
