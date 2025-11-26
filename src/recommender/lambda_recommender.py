"""
AWS Cost Recommender Lambda Function

Analyzes cost data and generates optimization recommendations.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

# Import from Lambda Layer
from shared.schemas import parse_cost_history_item
from shared.routers.cost_history_router import cost_history_router
from shared.routers.cost_recommendations_router import cost_recommendations_router


def lambda_handler(event, context):
    """
    Main handler function for AWS Lambda.
    
    Generates cost optimization recommendations.
    
    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object
        
    Returns:
        dict: Response with status code and body
    """
    try:
        # Fetch recent cost data
        cost_data = fetch_recent_costs()
        
        if not cost_data:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No cost data available'})
            }
        
        # Analyze and generate recommendations
        recommendations = analyze_and_recommend(cost_data)
        
        # Store recommendations
        store_recommendations(recommendations)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Recommendations generated successfully',
                'count': len(recommendations)
            })
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def fetch_recent_costs():
    """
    Fetch recent cost data from DynamoDB using router.
    
    Returns:
        list: Recent cost records (excluding forecasts)
    """
    try:
        # Use router to scan, automatically excluding forecasts
        return cost_history_router.scan_all(exclude_forecast=True)
    except Exception as e:
        print(f"Error fetching costs: {e}")
        return []


def analyze_and_recommend(cost_data):
    """
    Analyze cost data and generate recommendations.
    Data is already filtered by router to exclude forecast records.
    
    Args:
        cost_data: List of cost records from DynamoDB (no forecasts)
        
    Returns:
        list: Cost optimization recommendations
    """
    recommendations = []
    
    # Aggregate costs by service (data already filtered by router)
    service_costs = {}
    for record in cost_data:
        service = record.get('service_name', 'Unknown')  # Blueprint uses service_name
        cost = float(record.get('cost_usd', 0))  # Blueprint uses cost_usd
        
        if service not in service_costs:
            service_costs[service] = 0
        service_costs[service] += cost
    
    # Generate recommendations based on high-cost services
    sorted_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)
    
    for service, total_cost in sorted_services[:5]:  # Top 5 services
        recommendation = generate_service_recommendation(service, total_cost)
        if recommendation:
            recommendations.append(recommendation)
    
    return recommendations


def generate_service_recommendation(service, total_cost):
    """
    Generate recommendation for a specific service.
    
    Args:
        service: AWS service name
        total_cost: Total cost for the service
        
    Returns:
        dict: Recommendation record
    """
    # Recommendation logic based on service type
    recommendations_map = {
        'Amazon Elastic Compute Cloud - Compute': {
            'title': 'EC2 Instance Optimization',
            'description': 'Consider using Reserved Instances or Savings Plans for consistent workloads',
            'potential_savings': total_cost * 0.30,  # 30% potential savings
            'priority': 'high' if total_cost > 1000 else 'medium'
        },
        'Amazon Simple Storage Service': {
            'title': 'S3 Storage Class Optimization',
            'description': 'Move infrequently accessed data to S3 Glacier or Intelligent-Tiering',
            'potential_savings': total_cost * 0.40,
            'priority': 'medium'
        },
        'Amazon Relational Database Service': {
            'title': 'RDS Instance Right-Sizing',
            'description': 'Review database instance sizes and consider Reserved Instances',
            'potential_savings': total_cost * 0.25,
            'priority': 'high' if total_cost > 500 else 'medium'
        }
    }
    
    recommendation_template = recommendations_map.get(service, {
        'title': f'Review {service} Usage',
        'description': f'Analyze usage patterns and consider optimization opportunities',
        'potential_savings': total_cost * 0.15,
        'priority': 'low'
    })
    
    # Generate UUID for recommendation_id
    import uuid
    recommendation_id = str(uuid.uuid4())
    
    # Determine recommendation_type based on service characteristics
    if total_cost > 100:
        rec_type = 'RIGHT_SIZE'
    else:
        rec_type = 'UNUSED_RESOURCE'
    
    # Calculate TTL (180 days from now for recommendations)
    from datetime import timedelta
    ttl = int((datetime.now() + timedelta(days=180)).timestamp())
    
    # Make SK unique by combining date + timestamp to avoid duplicate key errors
    # Multiple services can have same recommendation_type on same day
    generated_date_unique = f"{datetime.now().strftime('%Y-%m-%d')}#{recommendation_id[:8]}"
    
    return {
        'recommendation_type': rec_type,  # PK in blueprint schema
        'generated_date': generated_date_unique,  # SK - made unique with UUID fragment
        'recommendation_id': recommendation_id,
        'service_name': service,  # Blueprint uses service_name
        'current_cost': Decimal(str(round(total_cost, 2))),
        'potential_savings': Decimal(str(round(recommendation_template['potential_savings'], 2))),
        'savings_percent': Decimal(str(round((recommendation_template['potential_savings'] / total_cost) * 100, 1))),
        'recommendation': recommendation_template['description'],
        'priority': recommendation_template['priority'],
        'confidence': 'HIGH',
        'implementation_effort': 'MEDIUM',
        'status': 'NEW',
        'created_at': datetime.now().isoformat(),
        'ttl': ttl
    }


def store_recommendations(recommendations):
    """
    Store recommendations in DynamoDB using router.
    
    Args:
        recommendations: List of recommendation records
    """
    try:
        # Use router for batch storage
        stored_count = cost_recommendations_router.put_batch(recommendations)
        
        if stored_count != len(recommendations):
            print(f"Warning: Only {stored_count}/{len(recommendations)} recommendations stored successfully")
    except Exception as e:
        print(f"Error storing recommendations: {e}")
