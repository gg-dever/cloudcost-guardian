"""
AWS Cost Notifier Lambda Function

Sends alerts and notifications based on cost thresholds and anomalies.
"""

import json
import os
import sys
from datetime import datetime
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

# Import from Lambda Layer
from shared.schemas import parse_cost_history_item
from shared.routers.cost_history_router import cost_history_router
from shared.routers.cost_anomalies_router import cost_anomalies_router


# Initialize AWS clients
sns_client = boto3.client('sns')

# Configuration
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
COST_THRESHOLD = float(os.environ.get('DAILY_COST_THRESHOLD', '100'))


def lambda_handler(event, context):
    """
    Main handler function for AWS Lambda.
    
    Checks for cost anomalies and sends notifications.
    
    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object
        
    Returns:
        dict: Response with status code and body
    """
    try:
        # Fetch today's costs
        daily_costs = fetch_daily_costs()
        
        if not daily_costs:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No cost data available'})
            }
        
        # Check for alerts
        alerts = check_cost_alerts(daily_costs)
        
        # Store anomalies in DynamoDB and send notifications
        if alerts:
            store_anomalies(alerts)
            send_notifications(alerts)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Notification check completed',
                'alerts_sent': len(alerts)
            })
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def fetch_daily_costs():
    """
    Fetch today's ACTUAL cost data from DynamoDB using router.
    Excludes forecast data (service_name='FORECAST') to prevent false alerts.
    
    Returns:
        list: Today's actual cost records (excluding forecasts)
    """
    try:
        today = datetime.now().date().strftime('%Y-%m-%d')
        
        # Use router to query with automatic FORECAST exclusion
        actual_costs = cost_history_router.query_by_date(today, exclude_forecast=True)
        
        return actual_costs
        
    except Exception as e:
        print(f"Error fetching daily costs: {e}")
        return []


def check_cost_alerts(daily_costs):
    """
    Check if cost thresholds have been exceeded.
    
    Args:
        daily_costs: List of today's cost records
        
    Returns:
        list: Alert messages
    """
    alerts = []
    
    # Calculate total daily cost using blueprint schema
    total_cost = sum(float(item.get('cost_usd', 0)) for item in daily_costs)
    
    # Check threshold
    if total_cost > COST_THRESHOLD:
        alerts.append({
            'type': 'DAILY_SPIKE',  # Blueprint anomaly_type
            'severity': 'HIGH',
            'message': f'Daily cost threshold exceeded: ${total_cost:.2f} (Threshold: ${COST_THRESHOLD:.2f})',
            'total_cost': total_cost,
            'threshold': COST_THRESHOLD
        })
    
    # Check for unusual service costs using blueprint schema
    service_costs = {}
    for record in daily_costs:
        service = record.get('service_name', 'Unknown')  # Blueprint uses service_name
        cost = float(record.get('cost_usd', 0))  # Blueprint uses cost_usd
        service_costs[service] = service_costs.get(service, 0) + cost
    
    # Alert on services costing > $50
    for service, cost in service_costs.items():
        if cost > 50:
            alerts.append({
                'type': 'SERVICE_SPIKE',  # Blueprint anomaly_type
                'severity': 'MEDIUM',
                'message': f'High cost detected for {service}: ${cost:.2f}',
                'service': service,
                'cost': cost
            })
    
    return alerts


def store_anomalies(alerts):
    """
    Store detected anomalies in DynamoDB using router.
    
    Args:
        alerts: List of alert dictionaries
    """
    try:
        stored_count = 0
        
        for alert in alerts:
            # Prepare optional parameters based on alert type
            service_name = alert.get('service') if alert['type'] == 'SERVICE_SPIKE' else None
            cost_usd = Decimal(str(round(alert['cost'], 2))) if 'cost' in alert else None
            total_cost = Decimal(str(round(alert['total_cost'], 2))) if 'total_cost' in alert else None
            threshold = Decimal(str(round(alert['threshold'], 2))) if 'threshold' in alert else None
            
            # Use router to create anomaly
            result = cost_anomalies_router.create_anomaly(
                anomaly_type=alert['type'],
                severity=alert['severity'],
                message=alert['message'],
                service_name=service_name,
                cost_usd=cost_usd,
                total_cost=total_cost,
                threshold=threshold,
                ttl_days=90
            )
            
            if result:
                stored_count += 1
        
        print(f"Stored {stored_count}/{len(alerts)} anomalies in DynamoDB")
        
    except Exception as e:
        print(f"Error storing anomalies: {e}")


def send_notifications(alerts):
    """
    Send notifications via SNS.
    
    Args:
        alerts: List of alert messages
    """
    if not SNS_TOPIC_ARN:
        print("SNS_TOPIC_ARN not configured")
        return
    
    for alert in alerts:
        try:
            subject = f"AWS Cost Alert: {alert['type']}"
            message = format_alert_message(alert)
            
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=subject,
                Message=message
            )
            
            print(f"Sent notification: {subject}")
            
        except ClientError as e:
            print(f"Error sending notification: {e}")


def format_alert_message(alert):
    """
    Format alert data into a readable message.
    
    Args:
        alert: Alert dictionary
        
    Returns:
        str: Formatted message
    """
    message = f"""
AWS Cost Guardian Alert
=======================

Type: {alert['type']}
Severity: {alert['severity']}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

{alert['message']}

"""
    
    if alert['type'] == 'threshold_exceeded':
        message += f"""
Total Daily Cost: ${alert['total_cost']:.2f}
Alert Threshold: ${alert['threshold']:.2f}
Overage: ${alert['total_cost'] - alert['threshold']:.2f}
"""
    
    elif alert['type'] == 'high_service_cost':
        message += f"""
Service: {alert['service']}
Cost: ${alert['cost']:.2f}
"""
    
    message += "\nPlease review your AWS Cost Guardian dashboard for more details."
    
    return message
