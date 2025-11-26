"""
DynamoDB Router for cost_anomalies table.

Centralizes all database operations for the cost_anomalies table,
including reads, writes, queries, and scans.
"""

import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from shared.schemas import CostAnomalyRecord, TableNames


class CostAnomaliesRouter:
    """Router for cost_anomalies table operations."""
    
    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize the cost_anomalies router.
        
        Args:
            table_name: Optional table name override (defaults to env var or 'cost_anomalies')
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = table_name or os.environ.get('ANOMALIES_TABLE', TableNames.COST_ANOMALIES)
        self.table = self.dynamodb.Table(self.table_name)
    
    def create_anomaly(
        self,
        anomaly_type: str,
        severity: str,
        message: str,
        service_name: Optional[str] = None,
        cost_usd: Optional[Decimal] = None,
        total_cost: Optional[Decimal] = None,
        threshold: Optional[Decimal] = None,
        ttl_days: int = 90
    ) -> Optional[Dict[str, Any]]:
        """
        Create and store a new anomaly record.
        
        Args:
            anomaly_type: Type of anomaly (DAILY_SPIKE, SERVICE_SPIKE, etc.)
            severity: Severity level (HIGH, MEDIUM, LOW)
            message: Descriptive message about the anomaly
            service_name: Optional service name for service-specific anomalies
            cost_usd: Optional cost amount for the anomaly
            total_cost: Optional total cost for threshold anomalies
            threshold: Optional threshold value that was exceeded
            ttl_days: Days until record expires (default: 90)
            
        Returns:
            dict: The created anomaly record or None if failed
        """
        try:
            # Calculate TTL
            ttl = int((datetime.now() + timedelta(days=ttl_days)).timestamp())
            
            # Create unique detection_date with UUID fragment to avoid duplicates
            detection_date = f"{datetime.now().strftime('%Y-%m-%d')}#{str(uuid.uuid4())[:8]}"
            
            anomaly = {
                'anomaly_type': anomaly_type,  # PK
                'detection_date': detection_date,  # SK
                'severity': severity,
                'message': message,
                'detected_at': datetime.now().isoformat(),
                'ttl': ttl
            }
            
            # Add optional fields
            if service_name:
                anomaly['service_name'] = service_name
            if cost_usd is not None:
                anomaly['cost_usd'] = cost_usd
            if total_cost is not None:
                anomaly['total_cost'] = total_cost
            if threshold is not None:
                anomaly['threshold'] = threshold
            
            self.table.put_item(Item=anomaly)
            print(f"Created anomaly: {anomaly_type} - {detection_date}")
            
            return anomaly
            
        except ClientError as e:
            print(f"Error creating anomaly: {e}")
            return None
    
    def put_batch(self, anomalies: List[Dict[str, Any]]) -> int:
        """
        Store multiple anomaly records in batch.
        
        Args:
            anomalies: List of anomaly dictionaries
            
        Returns:
            int: Number of records successfully stored
        """
        try:
            stored_count = 0
            with self.table.batch_writer() as batch:
                for anomaly in anomalies:
                    # Ensure unique detection_date
                    if '#' not in anomaly.get('detection_date', ''):
                        detection_date = f"{anomaly.get('detection_date', datetime.now().strftime('%Y-%m-%d'))}#{str(uuid.uuid4())[:8]}"
                        anomaly['detection_date'] = detection_date
                    
                    batch.put_item(Item=anomaly)
                    stored_count += 1
            
            print(f"Successfully stored {stored_count} anomaly records")
            return stored_count
            
        except ClientError as e:
            print(f"Error storing batch of anomalies: {e}")
            return 0
    
    def query_by_type(
        self, 
        anomaly_type: str, 
        limit: Optional[int] = None,
        date_from: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query anomalies by type.
        
        Args:
            anomaly_type: Type of anomaly (DAILY_SPIKE, SERVICE_SPIKE, etc.)
            limit: Optional limit on number of records
            date_from: Optional start date in YYYY-MM-DD format
            
        Returns:
            list: Anomaly records matching the type
        """
        try:
            query_kwargs = {
                'KeyConditionExpression': Key('anomaly_type').eq(anomaly_type)
            }
            
            if date_from:
                query_kwargs['KeyConditionExpression'] &= Key('detection_date').gte(date_from)
            
            if limit:
                query_kwargs['Limit'] = limit
            
            response = self.table.query(**query_kwargs)
            items = response.get('Items', [])
            
            print(f"Fetched {len(items)} anomalies of type: {anomaly_type}")
            return items
            
        except ClientError as e:
            print(f"Error querying anomalies by type: {e}")
            return []
    
    def query_recent(self, days: int = 7, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query recent anomalies.
        
        Args:
            days: Number of days to look back (default: 7)
            severity: Optional severity filter (HIGH, MEDIUM, LOW)
            
        Returns:
            list: Recent anomaly records
        """
        try:
            cutoff_date = (datetime.now().date() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            scan_kwargs = {
                'FilterExpression': Attr('detection_date').gte(cutoff_date)
            }
            
            if severity:
                scan_kwargs['FilterExpression'] &= Attr('severity').eq(severity)
            
            response = self.table.scan(**scan_kwargs)
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = self.table.scan(**scan_kwargs)
                items.extend(response.get('Items', []))
            
            # Sort by detection_date descending
            items.sort(key=lambda x: x.get('detection_date', ''), reverse=True)
            
            print(f"Fetched {len(items)} recent anomalies (last {days} days)")
            return items
            
        except ClientError as e:
            print(f"Error querying recent anomalies: {e}")
            return []
    
    def scan_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scan all anomaly records.
        
        Args:
            limit: Optional limit on number of records returned
            
        Returns:
            list: All anomaly records
        """
        try:
            scan_kwargs = {}
            if limit:
                scan_kwargs['Limit'] = limit
            
            response = self.table.scan(**scan_kwargs)
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response and (not limit or len(items) < limit):
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = self.table.scan(**scan_kwargs)
                items.extend(response.get('Items', []))
            
            print(f"Scanned {len(items)} anomaly records")
            return items
            
        except ClientError as e:
            print(f"Error scanning anomalies: {e}")
            return []
    
    def get_by_service(self, service_name: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get anomalies for a specific service.
        
        Args:
            service_name: AWS service name
            days: Number of days to look back (default: 30)
            
        Returns:
            list: Anomaly records for the service
        """
        try:
            cutoff_date = (datetime.now().date() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            response = self.table.scan(
                FilterExpression=Attr('service_name').eq(service_name) & Attr('detection_date').gte(cutoff_date)
            )
            
            items = response.get('Items', [])
            print(f"Fetched {len(items)} anomalies for service: {service_name}")
            return items
            
        except ClientError as e:
            print(f"Error querying anomalies by service: {e}")
            return []
    
    def delete_anomaly(self, anomaly_type: str, detection_date: str) -> bool:
        """
        Delete a specific anomaly record.
        
        Args:
            anomaly_type: Anomaly type (PK)
            detection_date: Detection date (SK)
            
        Returns:
            bool: True if successful
        """
        try:
            self.table.delete_item(
                Key={
                    'anomaly_type': anomaly_type,
                    'detection_date': detection_date
                }
            )
            print(f"Deleted anomaly: {anomaly_type} - {detection_date}")
            return True
            
        except ClientError as e:
            print(f"Error deleting anomaly: {e}")
            return False
    
    def get_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get summary statistics for anomalies.
        
        Args:
            days: Number of days to analyze (default: 30)
            
        Returns:
            dict: Summary statistics
        """
        anomalies = self.query_recent(days=days)
        
        summary = {
            'total_count': len(anomalies),
            'by_type': {},
            'by_severity': {},
            'high_severity_count': 0
        }
        
        for anomaly in anomalies:
            # Count by type
            anom_type = anomaly.get('anomaly_type', 'Unknown')
            summary['by_type'][anom_type] = summary['by_type'].get(anom_type, 0) + 1
            
            # Count by severity
            severity = anomaly.get('severity', 'Unknown')
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            if severity == 'HIGH':
                summary['high_severity_count'] += 1
        
        return summary


# Singleton instance for easy importing
cost_anomalies_router = CostAnomaliesRouter()
