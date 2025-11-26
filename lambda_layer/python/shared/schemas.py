"""
DynamoDB Schema Definitions for CloudCost Guardian

Provides type-safe data classes and constants for DynamoDB tables.
Aligns with blueprint schema in docs/data-model.md
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Literal
from datetime import datetime, timedelta


# ===================================
# TABLE NAMES
# ===================================

class TableNames:
    """DynamoDB table name constants"""
    COST_HISTORY = "cost_history"
    COST_ANOMALIES = "cost_anomalies"
    COST_RECOMMENDATIONS = "cost_recommendations"


# ===================================
# COST HISTORY TABLE
# ===================================

@dataclass
class CostHistoryRecord:
    """
    Schema for cost_history table
    
    PK: date (YYYY-MM-DD)
    SK: service_name
    TTL: 90 days
    """
    date: str  # PK: YYYY-MM-DD format
    service_name: str  # SK: AWS service name or 'FORECAST'
    cost_usd: Decimal
    usage_quantity: Optional[Decimal] = None
    ttl: Optional[int] = None
    
    # Forecast-specific fields
    confidence: Optional[Literal["high", "medium", "low"]] = None
    source: Optional[str] = None  # 'aws_cost_explorer'
    forecast_generated_at: Optional[str] = None
    
    @classmethod
    def create_ttl(cls, days: int = 90) -> int:
        """Generate TTL timestamp (days from now)"""
        return int((datetime.now() + timedelta(days=days)).timestamp())
    
    @classmethod
    def from_cost_explorer_response(cls, group: dict, date: str) -> 'CostHistoryRecord':
        """
        Create record from AWS Cost Explorer API response
        
        Args:
            group: Single group from ResultsByTime[].Groups[]
            date: Date string from TimePeriod.Start
            
        Example API Response Structure:
            {
                'Keys': ['Amazon EC2'],
                'Metrics': {
                    'UnblendedCost': {'Amount': '45.23', 'Unit': 'USD'},
                    'UsageQuantity': {'Amount': '720.5', 'Unit': 'N/A'}
                }
            }
        """
        service_name = group['Keys'][0] if group.get('Keys') else 'Unknown'
        cost = group.get('Metrics', {}).get('UnblendedCost', {}).get('Amount', '0')
        usage = group.get('Metrics', {}).get('UsageQuantity', {}).get('Amount')
        
        return cls(
            date=date,
            service_name=service_name,
            cost_usd=Decimal(str(cost)),
            usage_quantity=Decimal(str(usage)) if usage else None,
            ttl=cls.create_ttl(90)
        )
    
    @classmethod
    def from_forecast_response(cls, forecast_entry: dict) -> 'CostHistoryRecord':
        """
        Create forecast record from AWS GetCostForecast API response
        
        Args:
            forecast_entry: Single entry from ForecastResultsByTime[]
            
        Example API Response Structure:
            {
                'TimePeriod': {'Start': '2025-12-01', 'End': '2025-12-02'},
                'MeanValue': '0.79',
                'PredictionIntervalLowerBound': '0.65',
                'PredictionIntervalUpperBound': '0.93'
            }
        """
        date = forecast_entry.get('TimePeriod', {}).get('Start', '')
        mean_value = forecast_entry.get('MeanValue', '0')
        
        return cls(
            date=date,
            service_name='FORECAST',
            cost_usd=Decimal(str(mean_value)),
            confidence='high',  # AWS uses 80% prediction interval
            source='aws_cost_explorer',
            forecast_generated_at=datetime.now().isoformat(),
            ttl=cls.create_ttl(90)
        )
    
    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format"""
        item = {
            'date': self.date,
            'service_name': self.service_name,
            'cost_usd': self.cost_usd,
        }
        
        if self.usage_quantity is not None:
            item['usage_quantity'] = self.usage_quantity
        if self.ttl:
            item['ttl'] = self.ttl
        if self.confidence:
            item['confidence'] = self.confidence
        if self.source:
            item['source'] = self.source
        if self.forecast_generated_at:
            item['forecast_generated_at'] = self.forecast_generated_at
            
        return item


# ===================================
# COST ANOMALIES TABLE
# ===================================

@dataclass
class CostAnomalyRecord:
    """
    Schema for cost_anomalies table
    
    PK: anomaly_type (DAILY_SPIKE, SERVICE_SPIKE)
    SK: detection_date (YYYY-MM-DD#uuid)
    TTL: 90 days
    """
    anomaly_type: Literal["DAILY_SPIKE", "SERVICE_SPIKE"]  # PK
    detection_date: str  # SK: YYYY-MM-DD#uuid
    severity: Literal["critical", "warning", "info"]
    message: str
    detected_at: str  # ISO 8601 timestamp
    ttl: int
    
    # Service-specific fields (for SERVICE_SPIKE)
    service_name: Optional[str] = None
    cost_usd: Optional[Decimal] = None
    
    # Threshold fields (for DAILY_SPIKE)
    threshold_amount: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    
    @classmethod
    def create_detection_date(cls, uuid_fragment: str) -> str:
        """Create unique detection_date with UUID fragment"""
        today = datetime.now().strftime('%Y-%m-%d')
        return f"{today}#{uuid_fragment[:8]}"
    
    @classmethod
    def create_ttl(cls, days: int = 90) -> int:
        """Generate TTL timestamp (days from now)"""
        return int((datetime.now() + timedelta(days=days)).timestamp())
    
    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format"""
        item = {
            'anomaly_type': self.anomaly_type,
            'detection_date': self.detection_date,
            'severity': self.severity,
            'message': self.message,
            'detected_at': self.detected_at,
            'ttl': self.ttl,
        }
        
        # Add optional fields
        if self.service_name:
            item['service_name'] = self.service_name
        if self.cost_usd is not None:
            item['cost_usd'] = self.cost_usd
        if self.threshold_amount is not None:
            item['threshold_amount'] = self.threshold_amount
        if self.actual_amount is not None:
            item['actual_amount'] = self.actual_amount
            
        return item


# ===================================
# COST RECOMMENDATIONS TABLE
# ===================================

@dataclass
class CostRecommendationRecord:
    """
    Schema for cost_recommendations table
    
    PK: recommendation_type (RIGHT_SIZE, UNUSED_RESOURCE, etc.)
    SK: generated_date (YYYY-MM-DD#uuid)
    TTL: 180 days
    """
    recommendation_type: Literal["RIGHT_SIZE", "UNUSED_RESOURCE", "SAVINGS_PLAN", "RESERVED_INSTANCE"]  # PK
    generated_date: str  # SK: YYYY-MM-DD#uuid
    recommendation_id: str  # Full UUID
    service_name: str
    current_cost: Decimal
    potential_savings: Decimal
    savings_percent: Decimal
    recommendation: str
    priority: Literal["high", "medium", "low"]
    ttl: int
    created_at: Optional[str] = None  # ISO 8601 timestamp
    
    @classmethod
    def create_generated_date(cls, uuid_fragment: str) -> str:
        """Create unique generated_date with UUID fragment"""
        today = datetime.now().strftime('%Y-%m-%d')
        return f"{today}#{uuid_fragment[:8]}"
    
    @classmethod
    def create_ttl(cls, days: int = 180) -> int:
        """Generate TTL timestamp (days from now)"""
        return int((datetime.now() + timedelta(days=days)).timestamp())
    
    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format"""
        item = {
            'recommendation_type': self.recommendation_type,
            'generated_date': self.generated_date,
            'recommendation_id': self.recommendation_id,
            'service_name': self.service_name,
            'current_cost': self.current_cost,
            'potential_savings': self.potential_savings,
            'savings_percent': self.savings_percent,
            'recommendation': self.recommendation,
            'priority': self.priority,
            'ttl': self.ttl,
        }
        
        if self.created_at:
            item['created_at'] = self.created_at
            
        return item


# ===================================
# HELPER FUNCTIONS
# ===================================

def parse_cost_history_item(item: dict) -> CostHistoryRecord:
    """Parse DynamoDB item into CostHistoryRecord"""
    return CostHistoryRecord(
        date=item['date'],
        service_name=item['service_name'],
        cost_usd=Decimal(str(item['cost_usd'])),
        usage_quantity=Decimal(str(item['usage_quantity'])) if 'usage_quantity' in item else None,
        ttl=int(item['ttl']) if 'ttl' in item else None,
        confidence=item.get('confidence'),
        source=item.get('source'),
        forecast_generated_at=item.get('forecast_generated_at'),
    )


def parse_anomaly_item(item: dict) -> CostAnomalyRecord:
    """Parse DynamoDB item into CostAnomalyRecord"""
    return CostAnomalyRecord(
        anomaly_type=item['anomaly_type'],
        detection_date=item['detection_date'],
        severity=item['severity'],
        message=item['message'],
        detected_at=item['detected_at'],
        ttl=int(item['ttl']),
        service_name=item.get('service_name'),
        cost_usd=Decimal(str(item['cost_usd'])) if 'cost_usd' in item else None,
        threshold_amount=Decimal(str(item['threshold_amount'])) if 'threshold_amount' in item else None,
        actual_amount=Decimal(str(item['actual_amount'])) if 'actual_amount' in item else None,
    )


def parse_recommendation_item(item: dict) -> CostRecommendationRecord:
    """Parse DynamoDB item into CostRecommendationRecord"""
    return CostRecommendationRecord(
        recommendation_type=item['recommendation_type'],
        generated_date=item['generated_date'],
        recommendation_id=item['recommendation_id'],
        service_name=item['service_name'],
        current_cost=Decimal(str(item['current_cost'])),
        potential_savings=Decimal(str(item['potential_savings'])),
        savings_percent=Decimal(str(item['savings_percent'])),
        recommendation=item['recommendation'],
        priority=item['priority'],
        ttl=int(item['ttl']),
        created_at=item.get('created_at'),
    )
