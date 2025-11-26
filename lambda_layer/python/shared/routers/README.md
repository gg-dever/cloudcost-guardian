# DynamoDB Routers

This directory contains dedicated router classes for each DynamoDB table in the CloudCost Guardian system.

## 📁 Structure

```
routers/
├── __init__.py                         # Package exports
├── cost_history_router.py              # Router for cost_history table
├── cost_anomalies_router.py            # Router for cost_anomalies table
└── cost_recommendations_router.py      # Router for cost_recommendations table
```

## 📊 Available Routers

### 1. CostHistoryRouter (`cost_history_router.py`)
Manages all operations for the `cost_history` table.

**Key Methods:**
- `put_record(record)` - Store a single cost history record
- `put_batch(records)` - Store multiple records in batch
- `query_by_date(date, exclude_forecast=False)` - Query costs for a specific date
- `query_by_service(date, service_name)` - Query specific service cost
- `query_date_range(start_date, end_date, exclude_forecast=False)` - Query date range
- `scan_all(exclude_forecast=False, limit=None)` - Scan all records
- `get_forecast_records(start_date=None)` - Get forecast predictions only
- `aggregate_by_service(start_date, end_date, exclude_forecast=True)` - Aggregate by service
- `get_daily_total(date, exclude_forecast=True)` - Get total cost for a day
- `delete_record(date, service_name)` - Delete a specific record

**Special Feature:** Automatic FORECAST data filtering with `exclude_forecast=True` parameter

### 2. CostAnomaliesRouter (`cost_anomalies_router.py`)
Manages all operations for the `cost_anomalies` table.

**Key Methods:**
- `create_anomaly(anomaly_type, severity, message, ...)` - Create new anomaly
- `put_batch(anomalies)` - Store multiple anomalies in batch
- `query_by_type(anomaly_type, limit=None, date_from=None)` - Query by anomaly type
- `query_recent(days=7, severity=None)` - Query recent anomalies
- `scan_all(limit=None)` - Scan all anomaly records
- `get_by_service(service_name, days=30)` - Get anomalies for specific service
- `delete_anomaly(anomaly_type, detection_date)` - Delete an anomaly
- `get_summary(days=30)` - Get summary statistics

**Anomaly Types:** `DAILY_SPIKE`, `SERVICE_SPIKE`, `UNUSUAL_PATTERN`

### 3. CostRecommendationsRouter (`cost_recommendations_router.py`)
Manages all operations for the `cost_recommendations` table.

**Key Methods:**
- `create_recommendation(recommendation_type, service_name, ...)` - Create new recommendation
- `put_batch(recommendations)` - Store multiple recommendations in batch
- `query_by_type(recommendation_type, limit=None, date_from=None)` - Query by type
- `query_recent(days=30, status=None, priority=None)` - Query recent recommendations
- `scan_all(limit=None)` - Scan all recommendations
- `get_by_service(service_name, status=None)` - Get recommendations for service
- `update_status(recommendation_type, generated_date, new_status)` - Update status
- `delete_recommendation(recommendation_type, generated_date)` - Delete recommendation
- `get_total_potential_savings(status='NEW')` - Calculate total savings potential
- `get_summary(days=30)` - Get summary statistics

**Recommendation Types:** `RIGHT_SIZE`, `UNUSED_RESOURCE`, `RESERVED_INSTANCE`, `SPOT_INSTANCE`

## 🚀 Usage

### Basic Import (Singleton Instances)
```python
from routers.cost_history_router import cost_history_router
from routers.cost_anomalies_router import cost_anomalies_router
from routers.cost_recommendations_router import cost_recommendations_router

# Use directly
records = cost_history_router.query_by_date('2025-11-24', exclude_forecast=True)
```

### Import via Shared Module
```python
from routers import (
    cost_history_router,
    cost_anomalies_router,
    cost_recommendations_router
)
```

### Custom Instance
```python
from routers import CostHistoryRouter

# Create custom router with different table name
custom_router = CostHistoryRouter(table_name='custom_cost_history')
```

## 📝 Examples

### Cost History Operations
```python
from routers.cost_history_router import cost_history_router
from datetime import datetime, timedelta

# Get today's actual costs (excluding forecasts)
today = datetime.now().strftime('%Y-%m-%d')
actual_costs = cost_history_router.query_by_date(today, exclude_forecast=True)

# Get total cost for yesterday
yesterday = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
total = cost_history_router.get_daily_total(yesterday)
print(f"Total cost: ${total}")

# Aggregate by service (last 30 days)
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
service_totals = cost_history_router.aggregate_by_service(start_date, end_date)
```

### Anomaly Operations
```python
from routers.cost_anomalies_router import cost_anomalies_router
from decimal import Decimal

# Create a new anomaly
cost_anomalies_router.create_anomaly(
    anomaly_type='SERVICE_SPIKE',
    severity='HIGH',
    message='Unusual spike in Lambda costs',
    service_name='AWS Lambda',
    cost_usd=Decimal('150.00')
)

# Get recent high severity anomalies
high_severity = cost_anomalies_router.query_recent(days=7, severity='HIGH')

# Get summary
summary = cost_anomalies_router.get_summary(days=30)
print(f"Total anomalies: {summary['total_count']}")
print(f"High severity: {summary['high_severity_count']}")
```

### Recommendation Operations
```python
from routers.cost_recommendations_router import cost_recommendations_router
from decimal import Decimal

# Create a new recommendation
cost_recommendations_router.create_recommendation(
    recommendation_type='RIGHT_SIZE',
    service_name='AWS Lambda',
    recommendation='Consider reducing memory allocation for low-traffic functions',
    current_cost=Decimal('100.00'),
    potential_savings=Decimal('25.00'),
    priority='high',
    confidence='HIGH'
)

# Get all NEW recommendations
new_recs = cost_recommendations_router.query_recent(days=30, status='NEW')

# Calculate total potential savings
total_savings = cost_recommendations_router.get_total_potential_savings(status='NEW')
print(f"Potential savings: ${total_savings}")

# Update recommendation status
cost_recommendations_router.update_status('RIGHT_SIZE', '2025-11-24#abc123', 'IN_PROGRESS')
```

## ✅ Benefits

1. **Centralized Operations**: All database operations for each table in one place
2. **Type Safety**: Clear method signatures with proper typing
3. **Automatic Filtering**: Built-in FORECAST exclusion in cost_history queries
4. **Error Handling**: Consistent error handling and logging
5. **Helper Methods**: Aggregations, summaries, and common operations built-in
6. **Easy Testing**: Mock-friendly singleton pattern
7. **Maintainability**: Single source of truth for each table's operations
8. **UUID Management**: Automatic unique key generation for composite keys

## 🔧 Lambda Function Integration

All Lambda functions use these routers:

- **cost_analyzer**: Uses `cost_history_router` for storing costs
- **forecaster**: Uses `cost_history_router` for storing forecasts
- **notifier**: Uses `cost_history_router` and `cost_anomalies_router`
- **recommender**: Uses `cost_history_router` and `cost_recommendations_router`

## 📚 Additional Resources

- Schema definitions: `../schemas.py`
- Usage examples: `/scripts/router_examples.py`
- Integration examples: Lambda function files in `src/*/lambda_function.py`
