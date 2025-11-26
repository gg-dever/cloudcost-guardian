"""
Example usage of schemas.py with REAL AWS API responses
Demonstrates how to map AWS Cost Explorer API data to DynamoDB schemas
"""

from decimal import Decimal
from datetime import datetime, timedelta
import uuid
import sys
import os
import boto3

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.schemas import (
    TableNames,
    CostHistoryRecord,
    CostAnomalyRecord,
    CostRecommendationRecord,
)


def example_cost_history_from_api():
    """Example: Creating cost history records from REAL AWS Cost Explorer API"""
    print("📊 Cost History from AWS Cost Explorer API:")
    
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        
        # Get yesterday's costs
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=1)
        
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost', 'UsageQuantity'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )
        
        if response['ResultsByTime']:
            result = response['ResultsByTime'][0]
            date = result['TimePeriod']['Start']
            
            print(f"  Date: {date}")
            print(f"  Services found: {len(result['Groups'])}")
            print()
            
            # Map API response to schema (show first 3 services)
            for group in result['Groups'][:3]:
                record = CostHistoryRecord.from_cost_explorer_response(group, date)
                item = record.to_dynamodb_item()
                
                print(f"    • {item['service_name']}: ${item['cost_usd']}")
            
            if len(result['Groups']) > 3:
                print(f"    ... and {len(result['Groups']) - 3} more services")
            
            print(f"\n  ✅ Ready to store in: {TableNames.COST_HISTORY}")
        else:
            print("  ⚠️  No cost data available for yesterday")
    
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    print()


def example_forecast_from_api():
    """Example: Creating forecast records from REAL AWS GetCostForecast API"""
    print("🔮 Forecast from AWS Cost Explorer API:")
    
    try:
        ce = boto3.client('ce', region_name='us-east-1')
        
        # Get 7-day forecast
        today = datetime.now().date()
        start_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (today + timedelta(days=8)).strftime('%Y-%m-%d')
        
        response = ce.get_cost_forecast(
            TimePeriod={'Start': start_date, 'End': end_date},
            Metric='UNBLENDED_COST',
            Granularity='DAILY',
            PredictionIntervalLevel=80
        )
        
        total = response.get('Total', {}).get('Amount', '0')
        print(f"  Total 7-day forecast: ${total}")
        print(f"  Daily predictions:")
        print()
        
        # Map API response to schema (show first 5 days)
        time_series = response.get('ForecastResultsByTime', [])
        for entry in time_series[:5]:
            record = CostHistoryRecord.from_forecast_response(entry)
            item = record.to_dynamodb_item()
            
            print(f"    • {item['date']}: ${item['cost_usd']} ({item['confidence']} confidence)")
        
        if len(time_series) > 5:
            print(f"    ... and {len(time_series) - 5} more days")
        
        print(f"\n  ✅ Ready to store in: {TableNames.COST_HISTORY}")
    
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        if "DataUnavailableException" in str(e):
            print("  ℹ️  Forecast requires at least 3 months of cost history")
    
    print()


def example_anomaly_from_dynamodb():
    """Example: Reading anomaly records from REAL DynamoDB table"""
    print("🚨 Anomalies from DynamoDB:")
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table(TableNames.COST_ANOMALIES)
        
        # Scan for recent anomalies
        response = table.scan(Limit=3)
        items = response.get('Items', [])
        
        if items:
            print(f"  Found {response['Count']} recent anomalies:")
            print()
            
            for item in items:
                print(f"    • Type: {item['anomaly_type']}")
                print(f"      Severity: {item['severity']}")
                print(f"      Message: {item['message']}")
                if 'service_name' in item:
                    print(f"      Service: {item['service_name']}")
                    print(f"      Cost: ${item.get('cost_usd', 'N/A')}")
                print()
            
            print(f"  ✅ Retrieved from: {TableNames.COST_ANOMALIES}")
        else:
            print("  ℹ️  No anomalies found (this is good!)")
            print(f"  📝 Creating example anomaly to demonstrate schema:")
            print()
            
            # Create example using schema
            uuid_fragment = str(uuid.uuid4())[:8]
            anomaly = CostAnomalyRecord(
                anomaly_type="SERVICE_SPIKE",
                detection_date=CostAnomalyRecord.create_detection_date(uuid_fragment),
                severity="warning",
                message="EC2 costs increased by 150%",
                detected_at=datetime.now().isoformat(),
                ttl=CostAnomalyRecord.create_ttl(90),
                service_name="Amazon EC2",
                cost_usd=Decimal("125.50")
            )
            item = anomaly.to_dynamodb_item()
            print(f"    • Type: {item['anomaly_type']}")
            print(f"      Message: {item['message']}")
            print(f"      Service: {item['service_name']}")
    
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    print()


def example_recommendation_from_dynamodb():
    """Example: Reading recommendation records from REAL DynamoDB table"""
    print("💡 Recommendations from DynamoDB:")
    
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table(TableNames.COST_RECOMMENDATIONS)
        
        # Scan for recent recommendations
        response = table.scan(Limit=3)
        items = response.get('Items', [])
        
        if items:
            print(f"  Found {response['Count']} recommendations:")
            print()
            
            for item in items:
                print(f"    • Type: {item['recommendation_type']}")
                print(f"      Service: {item['service_name']}")
                print(f"      Current Cost: ${item['current_cost']}")
                print(f"      Potential Savings: ${item['potential_savings']} ({item['savings_percent']}%)")
                print(f"      Priority: {item['priority']}")
                print(f"      Recommendation: {item['recommendation'][:60]}...")
                print()
            
            print(f"  ✅ Retrieved from: {TableNames.COST_RECOMMENDATIONS}")
        else:
            print("  ℹ️  No recommendations found yet")
            print(f"  📝 Creating example recommendation to demonstrate schema:")
            print()
            
            # Create example using schema
            recommendation_uuid = str(uuid.uuid4())
            recommendation = CostRecommendationRecord(
                recommendation_type="RIGHT_SIZE",
                generated_date=CostRecommendationRecord.create_generated_date(recommendation_uuid),
                recommendation_id=recommendation_uuid,
                service_name="Amazon EC2",
                current_cost=Decimal("150.00"),
                potential_savings=Decimal("45.00"),
                savings_percent=Decimal("30.0"),
                recommendation="Consider downsizing t3.large instances to t3.medium",
                priority="high",
                ttl=CostRecommendationRecord.create_ttl(180),
                created_at=datetime.now().isoformat()
            )
            item = recommendation.to_dynamodb_item()
            print(f"    • Type: {item['recommendation_type']}")
            print(f"      Savings: ${item['potential_savings']} ({item['savings_percent']}%)")
            print(f"      Priority: {item['priority']}")
    
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
    
    print()


if __name__ == "__main__":
    print("=" * 70)
    print("CloudCost Guardian - Schema Examples with REAL AWS API Data")
    print("=" * 70)
    print()
    
    example_cost_history_from_api()
    example_forecast_from_api()
    example_anomaly_from_dynamodb()
    example_recommendation_from_dynamodb()
    
    print("=" * 70)
    print("✅ All examples completed!")
    print()
    print("💡 These schemas can now be imported and used in your Lambda functions:")
    print("   from shared.schemas import CostHistoryRecord")
    print("   record = CostHistoryRecord.from_cost_explorer_response(group, date)")
    print("=" * 70)
