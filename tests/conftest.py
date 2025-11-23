"""
Pytest Configuration

Common fixtures and settings for all tests.
"""

import pytest
import os


@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['DYNAMODB_TABLE'] = 'cost-data'
    os.environ['COST_TABLE'] = 'cost-data'
    os.environ['FORECAST_TABLE'] = 'cost-forecasts'
    os.environ['RECOMMENDATIONS_TABLE'] = 'cost-recommendations'
    os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-topic'
    os.environ['DAILY_COST_THRESHOLD'] = '100'


@pytest.fixture
def aws_credentials():
    """Mock AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
