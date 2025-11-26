"""
Pytest configuration and shared fixtures for CloudCost Guardian tests.
"""
import os
import sys
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for testing."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def mock_env_vars():
    """Set up environment variables for Lambda functions."""
    os.environ['COST_HISTORY_TABLE'] = 'cost_history'
    os.environ['ANOMALIES_TABLE'] = 'cost_anomalies'
    os.environ['RECOMMENDATIONS_TABLE'] = 'cost_recommendations'
    os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-topic'
    os.environ['DAILY_COST_THRESHOLD'] = '100'


@pytest.fixture
def sample_cost_data():
    """Sample cost data for testing."""
    return [
        {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'service_name': 'AWS Lambda',
            'cost_usd': Decimal('25.50'),
            'usage_quantity': Decimal('1000')
        },
        {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'service_name': 'Amazon S3',
            'cost_usd': Decimal('15.75'),
            'usage_quantity': Decimal('500')
        }
    ]


@pytest.fixture
def sample_cost_explorer_response():
    """Sample AWS Cost Explorer API response."""
    today = datetime.now().strftime('%Y-%m-%d')
    return {
        'ResultsByTime': [
            {
                'TimePeriod': {
                    'Start': today,
                    'End': today
                },
                'Groups': [
                    {
                        'Keys': ['AWS Lambda'],
                        'Metrics': {
                            'UnblendedCost': {'Amount': '25.50', 'Unit': 'USD'},
                            'UsageQuantity': {'Amount': '1000', 'Unit': 'N/A'}
                        }
                    },
                    {
                        'Keys': ['Amazon S3'],
                        'Metrics': {
                            'UnblendedCost': {'Amount': '15.75', 'Unit': 'USD'},
                            'UsageQuantity': {'Amount': '500', 'Unit': 'N/A'}
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_forecast_response():
    """Sample AWS GetCostForecast API response."""
    tomorrow = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
    return {
        'Total': {
            'Amount': '50.00',
            'Unit': 'USD'
        },
        'ForecastResultsByTime': [
            {
                'TimePeriod': {
                    'Start': tomorrow,
                    'End': (datetime.now().date() + timedelta(days=2)).strftime('%Y-%m-%d')
                },
                'MeanValue': '0.79',
                'PredictionIntervalLowerBound': '0.65',
                'PredictionIntervalUpperBound': '0.93'
            }
        ]
    }
