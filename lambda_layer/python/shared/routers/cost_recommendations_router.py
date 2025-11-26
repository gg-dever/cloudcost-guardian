"""
DynamoDB Router for cost_recommendations table.

Centralizes all database operations for the cost_recommendations table,
including reads, writes, queries, and scans.
"""

import os
import uuid
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from shared.schemas import CostRecommendationRecord, TableNames


class CostRecommendationsRouter:
    """Router for cost_recommendations table operations."""
    
    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize the cost_recommendations router.
        
        Args:
            table_name: Optional table name override (defaults to env var or 'cost_recommendations')
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = table_name or os.environ.get('RECOMMENDATIONS_TABLE', TableNames.COST_RECOMMENDATIONS)
        self.table = self.dynamodb.Table(self.table_name)
    
    def create_recommendation(
        self,
        recommendation_type: str,
        service_name: str,
        recommendation: str,
        current_cost: Decimal,
        potential_savings: Decimal,
        priority: Literal['high', 'medium', 'low'] = 'medium',
        confidence: Literal['HIGH', 'MEDIUM', 'LOW'] = 'MEDIUM',
        implementation_effort: Literal['LOW', 'MEDIUM', 'HIGH'] = 'MEDIUM',
        status: Literal['NEW', 'IN_PROGRESS', 'COMPLETED', 'DISMISSED'] = 'NEW',
        ttl_days: int = 180
    ) -> Optional[Dict[str, Any]]:
        """
        Create and store a new recommendation record.
        
        Args:
            recommendation_type: Type of recommendation (RIGHT_SIZE, UNUSED_RESOURCE, etc.)
            service_name: AWS service name
            recommendation: Recommendation description
            current_cost: Current cost amount
            potential_savings: Estimated savings amount
            priority: Priority level (high, medium, low)
            confidence: Confidence level (HIGH, MEDIUM, LOW)
            implementation_effort: Implementation effort (LOW, MEDIUM, HIGH)
            status: Current status (NEW, IN_PROGRESS, COMPLETED, DISMISSED)
            ttl_days: Days until record expires (default: 180)
            
        Returns:
            dict: The created recommendation record or None if failed
        """
        try:
            # Generate unique IDs
            recommendation_id = str(uuid.uuid4())
            generated_date_unique = f"{datetime.now().strftime('%Y-%m-%d')}#{recommendation_id[:8]}"
            
            # Calculate savings percent
            savings_percent = Decimal('0')
            if current_cost > 0:
                savings_percent = (potential_savings / current_cost) * Decimal('100')
                savings_percent = savings_percent.quantize(Decimal('0.1'))
            
            # Calculate TTL
            ttl = int((datetime.now() + timedelta(days=ttl_days)).timestamp())
            
            record = {
                'recommendation_type': recommendation_type,  # PK
                'generated_date': generated_date_unique,  # SK (unique with UUID)
                'recommendation_id': recommendation_id,
                'service_name': service_name,
                'current_cost': current_cost,
                'potential_savings': potential_savings,
                'savings_percent': savings_percent,
                'recommendation': recommendation,
                'priority': priority,
                'confidence': confidence,
                'implementation_effort': implementation_effort,
                'status': status,
                'created_at': datetime.now().isoformat(),
                'ttl': ttl
            }
            
            self.table.put_item(Item=record)
            print(f"Created recommendation: {recommendation_type} for {service_name}")
            
            return record
            
        except ClientError as e:
            print(f"Error creating recommendation: {e}")
            return None
    
    def put_batch(self, recommendations: List[Dict[str, Any]]) -> int:
        """
        Store multiple recommendation records in batch.
        
        Args:
            recommendations: List of recommendation dictionaries
            
        Returns:
            int: Number of records successfully stored
        """
        try:
            stored_count = 0
            with self.table.batch_writer() as batch:
                for rec in recommendations:
                    # Ensure unique generated_date if not already present
                    if '#' not in rec.get('generated_date', ''):
                        rec_id = rec.get('recommendation_id', str(uuid.uuid4()))
                        generated_date = f"{rec.get('generated_date', datetime.now().strftime('%Y-%m-%d'))}#{rec_id[:8]}"
                        rec['generated_date'] = generated_date
                    
                    batch.put_item(Item=rec)
                    stored_count += 1
            
            print(f"Successfully stored {stored_count} recommendation records")
            return stored_count
            
        except ClientError as e:
            print(f"Error storing batch of recommendations: {e}")
            return 0
    
    def query_by_type(
        self, 
        recommendation_type: str, 
        limit: Optional[int] = None,
        date_from: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query recommendations by type.
        
        Args:
            recommendation_type: Type of recommendation (RIGHT_SIZE, UNUSED_RESOURCE, etc.)
            limit: Optional limit on number of records
            date_from: Optional start date in YYYY-MM-DD format
            
        Returns:
            list: Recommendation records matching the type
        """
        try:
            query_kwargs = {
                'KeyConditionExpression': Key('recommendation_type').eq(recommendation_type)
            }
            
            if date_from:
                query_kwargs['KeyConditionExpression'] &= Key('generated_date').gte(date_from)
            
            if limit:
                query_kwargs['Limit'] = limit
            
            response = self.table.query(**query_kwargs)
            items = response.get('Items', [])
            
            print(f"Fetched {len(items)} recommendations of type: {recommendation_type}")
            return items
            
        except ClientError as e:
            print(f"Error querying recommendations by type: {e}")
            return []
    
    def query_recent(
        self, 
        days: int = 30, 
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query recent recommendations.
        
        Args:
            days: Number of days to look back (default: 30)
            status: Optional status filter (NEW, IN_PROGRESS, COMPLETED, DISMISSED)
            priority: Optional priority filter (high, medium, low)
            
        Returns:
            list: Recent recommendation records
        """
        try:
            cutoff_date = (datetime.now().date() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            filter_expressions = [Attr('generated_date').gte(cutoff_date)]
            
            if status:
                filter_expressions.append(Attr('status').eq(status))
            if priority:
                filter_expressions.append(Attr('priority').eq(priority))
            
            # Combine filter expressions
            filter_expr = filter_expressions[0]
            for expr in filter_expressions[1:]:
                filter_expr &= expr
            
            response = self.table.scan(FilterExpression=filter_expr)
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    FilterExpression=filter_expr,
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response.get('Items', []))
            
            # Sort by generated_date descending
            items.sort(key=lambda x: x.get('generated_date', ''), reverse=True)
            
            print(f"Fetched {len(items)} recent recommendations (last {days} days)")
            return items
            
        except ClientError as e:
            print(f"Error querying recent recommendations: {e}")
            return []
    
    def scan_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scan all recommendation records.
        
        Args:
            limit: Optional limit on number of records returned
            
        Returns:
            list: All recommendation records
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
            
            print(f"Scanned {len(items)} recommendation records")
            return items
            
        except ClientError as e:
            print(f"Error scanning recommendations: {e}")
            return []
    
    def get_by_service(self, service_name: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recommendations for a specific service.
        
        Args:
            service_name: AWS service name
            status: Optional status filter
            
        Returns:
            list: Recommendation records for the service
        """
        try:
            filter_expr = Attr('service_name').eq(service_name)
            if status:
                filter_expr &= Attr('status').eq(status)
            
            response = self.table.scan(FilterExpression=filter_expr)
            items = response.get('Items', [])
            
            print(f"Fetched {len(items)} recommendations for service: {service_name}")
            return items
            
        except ClientError as e:
            print(f"Error querying recommendations by service: {e}")
            return []
    
    def update_status(
        self, 
        recommendation_type: str, 
        generated_date: str, 
        new_status: str
    ) -> bool:
        """
        Update the status of a recommendation.
        
        Args:
            recommendation_type: Recommendation type (PK)
            generated_date: Generated date (SK)
            new_status: New status value
            
        Returns:
            bool: True if successful
        """
        try:
            self.table.update_item(
                Key={
                    'recommendation_type': recommendation_type,
                    'generated_date': generated_date
                },
                UpdateExpression='SET #status = :status, updated_at = :updated',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': new_status,
                    ':updated': datetime.now().isoformat()
                }
            )
            print(f"Updated recommendation status to: {new_status}")
            return True
            
        except ClientError as e:
            print(f"Error updating recommendation status: {e}")
            return False
    
    def delete_recommendation(self, recommendation_type: str, generated_date: str) -> bool:
        """
        Delete a specific recommendation record.
        
        Args:
            recommendation_type: Recommendation type (PK)
            generated_date: Generated date (SK)
            
        Returns:
            bool: True if successful
        """
        try:
            self.table.delete_item(
                Key={
                    'recommendation_type': recommendation_type,
                    'generated_date': generated_date
                }
            )
            print(f"Deleted recommendation: {recommendation_type} - {generated_date}")
            return True
            
        except ClientError as e:
            print(f"Error deleting recommendation: {e}")
            return False
    
    def get_total_potential_savings(self, status: str = 'NEW') -> Decimal:
        """
        Calculate total potential savings from recommendations.
        
        Args:
            status: Status filter (default: NEW)
            
        Returns:
            Decimal: Total potential savings
        """
        try:
            recommendations = self.query_recent(days=180, status=status)
            total_savings = sum(
                Decimal(str(rec.get('potential_savings', 0))) 
                for rec in recommendations
            )
            return total_savings
            
        except Exception as e:
            print(f"Error calculating total savings: {e}")
            return Decimal('0')
    
    def get_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get summary statistics for recommendations.
        
        Args:
            days: Number of days to analyze (default: 30)
            
        Returns:
            dict: Summary statistics
        """
        recommendations = self.query_recent(days=days)
        
        summary = {
            'total_count': len(recommendations),
            'by_type': {},
            'by_status': {},
            'by_priority': {},
            'total_potential_savings': Decimal('0'),
            'high_priority_count': 0
        }
        
        for rec in recommendations:
            # Count by type
            rec_type = rec.get('recommendation_type', 'Unknown')
            summary['by_type'][rec_type] = summary['by_type'].get(rec_type, 0) + 1
            
            # Count by status
            status = rec.get('status', 'Unknown')
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
            
            # Count by priority
            priority = rec.get('priority', 'Unknown')
            summary['by_priority'][priority] = summary['by_priority'].get(priority, 0) + 1
            
            if priority == 'high':
                summary['high_priority_count'] += 1
            
            # Sum potential savings
            savings = Decimal(str(rec.get('potential_savings', 0)))
            summary['total_potential_savings'] += savings
        
        return summary


# Singleton instance for easy importing
cost_recommendations_router = CostRecommendationsRouter()
