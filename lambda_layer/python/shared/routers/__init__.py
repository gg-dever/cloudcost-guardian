"""
DynamoDB Routers Package

Provides dedicated router classes for each DynamoDB table:
- CostHistoryRouter: Operations for cost_history table
- CostAnomaliesRouter: Operations for cost_anomalies table
- CostRecommendationsRouter: Operations for cost_recommendations table

Each router centralizes all database operations for its respective table.
"""

from .cost_history_router import CostHistoryRouter, cost_history_router
from .cost_anomalies_router import CostAnomaliesRouter, cost_anomalies_router
from .cost_recommendations_router import CostRecommendationsRouter, cost_recommendations_router

__all__ = [
    # Router classes
    'CostHistoryRouter',
    'CostAnomaliesRouter',
    'CostRecommendationsRouter',
    # Singleton instances (ready to use)
    'cost_history_router',
    'cost_anomalies_router',
    'cost_recommendations_router',
]
