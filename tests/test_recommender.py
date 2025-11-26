"""
Tests for Recommender Lambda function.
"""
import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal


def test_lambda_handler_success(aws_credentials, mock_env_vars, sample_cost_data):
    """Test successful recommendation generation."""
    with patch('recommender.lambda_recommender.cost_history_router') as mock_router:
        mock_router.scan_all.return_value = sample_cost_data
        
        from recommender.lambda_recommender import lambda_handler
        
        response = lambda_handler({}, {})
        
        assert response['statusCode'] == 200
        assert 'count' in response['body']


def test_analyze_and_recommend(sample_cost_data):
    """Test recommendation analysis."""
    from recommender.lambda_recommender import analyze_and_recommend
    
    recommendations = analyze_and_recommend(sample_cost_data)
    
    # Should generate recommendations for services
    assert isinstance(recommendations, list)


def test_lambda_handler_no_data(aws_credentials, mock_env_vars):
    """Test handling when no cost data is available."""
    with patch('recommender.lambda_recommender.cost_history_router') as mock_router:
        mock_router.scan_all.return_value = []
        
        from recommender.lambda_recommender import lambda_handler
        
        response = lambda_handler({}, {})
        
        assert response['statusCode'] == 400


def test_generate_service_recommendation():
    """Test service-specific recommendation generation."""
    from recommender.lambda_recommender import generate_service_recommendation
    
    rec = generate_service_recommendation('Amazon Elastic Compute Cloud - Compute', 150.0)
    
    assert rec is not None
    assert 'recommendation_type' in rec
    assert 'potential_savings' in rec
    assert rec['service_name'] == 'Amazon Elastic Compute Cloud - Compute'
