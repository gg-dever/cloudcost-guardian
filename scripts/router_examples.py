#!/usr/bin/env python3
"""
Router Usage Examples

Demonstrates how to use the three DynamoDB routers:
- CostHistoryRouter (cost_history table)
- CostAnomaliesRouter (cost_anomalies table)
- CostRecommendationsRouter (cost_recommendations table)
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Add shared module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'shared'))

from routers.cost_history_router import cost_history_router
from routers.cost_anomalies_router import cost_anomalies_router
from routers.cost_recommendations_router import cost_recommendations_router


def example_cost_history_operations():
    """Examples of cost_history table operations."""
    print("=" * 70)
    print("COST HISTORY ROUTER EXAMPLES")
    print("=" * 70)
    
    # Example 1: Query costs for a specific date (excluding forecasts)
    print("\n1. Query costs for today (excluding forecasts):")
    today = datetime.now().date().strftime('%Y-%m-%d')
    records = cost_history_router.query_by_date(today, exclude_forecast=True)
    print(f"   Found {len(records)} actual cost records")
    
    # Example 2: Get daily total
    print("\n2. Get total cost for yesterday:")
    yesterday = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
    total = cost_history_router.get_daily_total(yesterday, exclude_forecast=True)
    print(f"   Total cost for {yesterday}: ${total}")
    
    # Example 3: Query date range
    print("\n3. Query last 7 days of costs:")
    end_date = datetime.now().date().strftime('%Y-%m-%d')
    start_date = (datetime.now().date() - timedelta(days=7)).strftime('%Y-%m-%d')
    records = cost_history_router.query_date_range(start_date, end_date, exclude_forecast=True)
    print(f"   Found {len(records)} records from {start_date} to {end_date}")
    
    # Example 4: Aggregate costs by service
    print("\n4. Aggregate costs by service (last 30 days):")
    end_date = datetime.now().date().strftime('%Y-%m-%d')
    start_date = (datetime.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
    service_totals = cost_history_router.aggregate_by_service(start_date, end_date)
    print(f"   Top 3 services:")
    sorted_services = sorted(service_totals.items(), key=lambda x: x[1], reverse=True)
    for service, cost in sorted_services[:3]:
        print(f"     - {service}: ${cost:.2f}")
    
    # Example 5: Get forecast records only
    print("\n5. Get all forecast records:")
    tomorrow = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
    forecasts = cost_history_router.get_forecast_records(start_date=tomorrow)
    print(f"   Found {len(forecasts)} forecast records from {tomorrow} onwards")
    
    # Example 6: Query specific service cost
    print("\n6. Query specific service cost:")
    service_record = cost_history_router.query_by_service(yesterday, 'AWS Lambda')
    if service_record:
        print(f"   AWS Lambda cost on {yesterday}: ${service_record.get('cost_usd', 0)}")
    else:
        print(f"   No AWS Lambda cost data for {yesterday}")


def example_anomalies_operations():
    """Examples of cost_anomalies table operations."""
    print("\n\n" + "=" * 70)
    print("COST ANOMALIES ROUTER EXAMPLES")
    print("=" * 70)
    
    # Example 1: Query recent anomalies
    print("\n1. Query recent anomalies (last 7 days):")
    recent_anomalies = cost_anomalies_router.query_recent(days=7)
    print(f"   Found {len(recent_anomalies)} anomalies in last 7 days")
    if recent_anomalies:
        print(f"   Latest: {recent_anomalies[0].get('message')}")
    
    # Example 2: Query high severity anomalies
    print("\n2. Query HIGH severity anomalies:")
    high_severity = cost_anomalies_router.query_recent(days=30, severity='HIGH')
    print(f"   Found {len(high_severity)} HIGH severity anomalies in last 30 days")
    
    # Example 3: Query by anomaly type
    print("\n3. Query DAILY_SPIKE anomalies:")
    daily_spikes = cost_anomalies_router.query_by_type('DAILY_SPIKE', limit=10)
    print(f"   Found {len(daily_spikes)} DAILY_SPIKE anomalies (showing up to 10)")
    
    # Example 4: Get anomalies for specific service
    print("\n4. Get anomalies for AWS Lambda:")
    lambda_anomalies = cost_anomalies_router.get_by_service('AWS Lambda', days=30)
    print(f"   Found {len(lambda_anomalies)} anomalies for AWS Lambda in last 30 days")
    
    # Example 5: Get anomaly summary
    print("\n5. Get anomaly summary (last 30 days):")
    summary = cost_anomalies_router.get_summary(days=30)
    print(f"   Total anomalies: {summary['total_count']}")
    print(f"   High severity: {summary['high_severity_count']}")
    print(f"   By type: {summary['by_type']}")
    print(f"   By severity: {summary['by_severity']}")
    
    # Example 6: Create a new anomaly (demonstration only - not executed)
    print("\n6. Example: Create a new anomaly (not executed):")
    print("   cost_anomalies_router.create_anomaly(")
    print("       anomaly_type='SERVICE_SPIKE',")
    print("       severity='MEDIUM',")
    print("       message='High cost detected for AWS Lambda: $75.00',")
    print("       service_name='AWS Lambda',")
    print("       cost_usd=Decimal('75.00')")
    print("   )")


def example_recommendations_operations():
    """Examples of cost_recommendations table operations."""
    print("\n\n" + "=" * 70)
    print("COST RECOMMENDATIONS ROUTER EXAMPLES")
    print("=" * 70)
    
    # Example 1: Query recent recommendations
    print("\n1. Query recent recommendations (last 30 days):")
    recent_recs = cost_recommendations_router.query_recent(days=30)
    print(f"   Found {len(recent_recs)} recommendations in last 30 days")
    if recent_recs:
        print(f"   Latest: {recent_recs[0].get('recommendation')}")
    
    # Example 2: Query NEW recommendations only
    print("\n2. Query NEW (unimplemented) recommendations:")
    new_recs = cost_recommendations_router.query_recent(days=30, status='NEW')
    print(f"   Found {len(new_recs)} NEW recommendations")
    
    # Example 3: Query high priority recommendations
    print("\n3. Query HIGH priority recommendations:")
    high_priority = cost_recommendations_router.query_recent(days=30, priority='high')
    print(f"   Found {len(high_priority)} high priority recommendations")
    
    # Example 4: Query by recommendation type
    print("\n4. Query RIGHT_SIZE recommendations:")
    right_size = cost_recommendations_router.query_by_type('RIGHT_SIZE', limit=10)
    print(f"   Found {len(right_size)} RIGHT_SIZE recommendations (showing up to 10)")
    
    # Example 5: Get recommendations for specific service
    print("\n5. Get recommendations for AWS Lambda:")
    lambda_recs = cost_recommendations_router.get_by_service('AWS Lambda')
    print(f"   Found {len(lambda_recs)} recommendations for AWS Lambda")
    
    # Example 6: Calculate total potential savings
    print("\n6. Calculate total potential savings (NEW recommendations):")
    total_savings = cost_recommendations_router.get_total_potential_savings(status='NEW')
    print(f"   Total potential savings: ${total_savings:.2f}")
    
    # Example 7: Get recommendation summary
    print("\n7. Get recommendation summary (last 30 days):")
    summary = cost_recommendations_router.get_summary(days=30)
    print(f"   Total recommendations: {summary['total_count']}")
    print(f"   High priority: {summary['high_priority_count']}")
    print(f"   By type: {summary['by_type']}")
    print(f"   By status: {summary['by_status']}")
    print(f"   Total potential savings: ${summary['total_potential_savings']:.2f}")
    
    # Example 8: Create a new recommendation (demonstration only - not executed)
    print("\n8. Example: Create a new recommendation (not executed):")
    print("   cost_recommendations_router.create_recommendation(")
    print("       recommendation_type='RIGHT_SIZE',")
    print("       service_name='AWS Lambda',")
    print("       recommendation='Consider reducing memory allocation',")
    print("       current_cost=Decimal('100.00'),")
    print("       potential_savings=Decimal('25.00'),")
    print("       priority='high',")
    print("       confidence='HIGH'")
    print("   )")


def main():
    """Run all router examples."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "DYNAMODB ROUTERS - USAGE EXAMPLES" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        example_cost_history_operations()
    except Exception as e:
        print(f"\n⚠️  Cost history examples error: {e}")
    
    try:
        example_anomalies_operations()
    except Exception as e:
        print(f"\n⚠️  Anomalies examples error: {e}")
    
    try:
        example_recommendations_operations()
    except Exception as e:
        print(f"\n⚠️  Recommendations examples error: {e}")
    
    print("\n" + "=" * 70)
    print("ROUTER BENEFITS")
    print("=" * 70)
    print("✅ Centralized database operations")
    print("✅ Type-safe methods with clear parameters")
    print("✅ Automatic FORECAST filtering in cost_history queries")
    print("✅ Built-in error handling and logging")
    print("✅ Consistent UUID generation for composite keys")
    print("✅ Helper methods for common operations (aggregations, summaries)")
    print("✅ Easy to test and mock for unit tests")
    print("✅ Single source of truth for each table's operations")
    print("\n")


if __name__ == '__main__':
    main()
