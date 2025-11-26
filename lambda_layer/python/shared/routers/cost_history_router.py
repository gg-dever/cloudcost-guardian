"""
DynamoDB Router for cost_history table.

Centralizes all database operations for the cost_history table,
including reads, writes, queries, and scans.
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from shared.schemas import CostHistoryRecord, TableNames


class CostHistoryRouter:
    """Router for cost_history table operations."""
    
    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize the cost_history router.
        
        Args:
            table_name: Optional table name override (defaults to env var or 'cost_history')
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = table_name or os.environ.get('COST_HISTORY_TABLE', TableNames.COST_HISTORY)
        self.table = self.dynamodb.Table(self.table_name)
    
    def put_record(self, record: CostHistoryRecord) -> bool:
        """
        Store a single cost history record.
        
        Args:
            record: CostHistoryRecord object to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            item = record.to_dynamodb_item()
            self.table.put_item(Item=item)
            return True
        except ClientError as e:
            print(f"Error storing cost history record: {e}")
            return False
    
    def put_batch(self, records: List[CostHistoryRecord]) -> int:
        """
        Store multiple cost history records in batch.
        
        Args:
            records: List of CostHistoryRecord objects
            
        Returns:
            int: Number of records successfully stored
        """
        try:
            stored_count = 0
            with self.table.batch_writer() as batch:
                for record in records:
                    item = record.to_dynamodb_item()
                    batch.put_item(Item=item)
                    stored_count += 1
            
            print(f"Successfully stored {stored_count} cost history records")
            return stored_count
        except ClientError as e:
            print(f"Error storing batch of cost history records: {e}")
            return 0
    
    def query_by_date(self, date: str, exclude_forecast: bool = False) -> List[Dict[str, Any]]:
        """
        Query cost records for a specific date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            exclude_forecast: If True, excludes records with service_name='FORECAST'
            
        Returns:
            list: Cost records for the specified date
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key('date').eq(date)
            )
            
            items = response.get('Items', [])
            
            # Filter out FORECAST data if requested
            if exclude_forecast:
                items = [item for item in items if item.get('service_name') != 'FORECAST']
                print(f"Fetched {len(items)} actual cost records for {date} (excluded forecast data)")
            else:
                print(f"Fetched {len(items)} cost records for {date}")
            
            return items
            
        except ClientError as e:
            print(f"Error querying cost history by date: {e}")
            return []
    
    def query_by_service(self, date: str, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Query a specific service's cost for a date.
        
        Args:
            date: Date string in YYYY-MM-DD format
            service_name: AWS service name
            
        Returns:
            dict: Cost record or None if not found
        """
        try:
            response = self.table.get_item(
                Key={
                    'date': date,
                    'service_name': service_name
                }
            )
            
            return response.get('Item')
            
        except ClientError as e:
            print(f"Error querying cost history by service: {e}")
            return None
    
    def query_date_range(
        self, 
        start_date: str, 
        end_date: str, 
        exclude_forecast: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query cost records for a date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            exclude_forecast: If True, excludes FORECAST records
            
        Returns:
            list: Cost records in the date range
        """
        try:
            all_records = []
            
            # Query each date in the range
            current = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            while current <= end:
                date_str = current.strftime('%Y-%m-%d')
                records = self.query_by_date(date_str, exclude_forecast=exclude_forecast)
                all_records.extend(records)
                current += timedelta(days=1)
            
            print(f"Fetched {len(all_records)} records from {start_date} to {end_date}")
            return all_records
            
        except Exception as e:
            print(f"Error querying date range: {e}")
            return []
    
    def scan_all(self, exclude_forecast: bool = False, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scan all cost history records.
        
        Args:
            exclude_forecast: If True, excludes FORECAST records
            limit: Optional limit on number of records returned
            
        Returns:
            list: All cost records
        """
        try:
            scan_kwargs = {}
            if limit:
                scan_kwargs['Limit'] = limit
            
            if exclude_forecast:
                scan_kwargs['FilterExpression'] = Attr('service_name').ne('FORECAST')
            
            response = self.table.scan(**scan_kwargs)
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response and (not limit or len(items) < limit):
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = self.table.scan(**scan_kwargs)
                items.extend(response.get('Items', []))
            
            print(f"Scanned {len(items)} cost history records")
            return items
            
        except ClientError as e:
            print(f"Error scanning cost history: {e}")
            return []
    
    def get_forecast_records(self, start_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all forecast records, optionally from a specific date forward.
        
        Args:
            start_date: Optional start date in YYYY-MM-DD format
            
        Returns:
            list: Forecast records
        """
        try:
            if start_date:
                # Query with date range
                filter_expr = Attr('service_name').eq('FORECAST') & Attr('date').gte(start_date)
            else:
                filter_expr = Attr('service_name').eq('FORECAST')
            
            response = self.table.scan(FilterExpression=filter_expr)
            items = response.get('Items', [])
            
            print(f"Fetched {len(items)} forecast records")
            return items
            
        except ClientError as e:
            print(f"Error fetching forecast records: {e}")
            return []
    
    def delete_record(self, date: str, service_name: str) -> bool:
        """
        Delete a specific cost record.
        
        Args:
            date: Date in YYYY-MM-DD format
            service_name: Service name
            
        Returns:
            bool: True if successful
        """
        try:
            self.table.delete_item(
                Key={
                    'date': date,
                    'service_name': service_name
                }
            )
            print(f"Deleted cost record: {date} - {service_name}")
            return True
            
        except ClientError as e:
            print(f"Error deleting cost record: {e}")
            return False
    
    def aggregate_by_service(
        self, 
        start_date: str, 
        end_date: str, 
        exclude_forecast: bool = True
    ) -> Dict[str, Decimal]:
        """
        Aggregate costs by service for a date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            exclude_forecast: If True, excludes FORECAST records
            
        Returns:
            dict: Service name to total cost mapping
        """
        records = self.query_date_range(start_date, end_date, exclude_forecast=exclude_forecast)
        
        service_totals = {}
        for record in records:
            service = record.get('service_name', 'Unknown')
            cost = Decimal(str(record.get('cost_usd', 0)))
            service_totals[service] = service_totals.get(service, Decimal('0')) + cost
        
        return service_totals
    
    def get_daily_total(self, date: str, exclude_forecast: bool = True) -> Decimal:
        """
        Get total cost for a specific day.
        
        Args:
            date: Date in YYYY-MM-DD format
            exclude_forecast: If True, excludes FORECAST records
            
        Returns:
            Decimal: Total cost for the day
        """
        records = self.query_by_date(date, exclude_forecast=exclude_forecast)
        total = sum(Decimal(str(record.get('cost_usd', 0))) for record in records)
        return total


# Singleton instance for easy importing
cost_history_router = CostHistoryRouter()
