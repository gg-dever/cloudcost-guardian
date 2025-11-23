# CloudCost Guardian Data Model

## Design Philosophy

**NoSQL Principle:** Design for your access patterns upfront.

Unlike SQL (PostgreSQL, MySQL) where you can query any column combination,
DynamoDB requires you to define HOW you'll query data when you design the table.

**Our Access Patterns:**

1. ✅ **Get all costs for a specific date**
   - Need: All service costs for 2024-01-15
   - Query: `PK = "2024-01-15"`

2. ✅ **Get cost for specific date + service**
   - Need: EC2 costs on 2024-01-15
   - Query: `PK = "2024-01-15" AND SK = "EC2"`

3. ✅ **Get recent anomalies**
   - Need: Last 7 days of anomalies
   - Query: `PK = "ANOMALY" AND SK BETWEEN "2024-01-08" AND "2024-01-15"`

4. ✅ **Get recommendations by type**
   - Need: All "RIGHT_SIZE" recommendations
   - Query: `PK = "RIGHT_SIZE"`

5. ❌ **Get all EC2 costs across all dates** (inefficient)
   - Would require scanning entire table - bad performance
   - Solution: This is OK for batch jobs (we run daily, can scan)

---

## Table 1: `cost_history`

**Purpose:** Store daily cost breakdown by AWS service

### Schema

**Primary Key:**
- **Partition Key (PK):** `date` (String, "YYYY-MM-DD")
- **Sort Key (SK):** `service_name` (String, e.g., "EC2", "S3")

**Attributes:**
- `cost_usd` (Number): Dollar amount spent
- `usage_quantity` (Number): Amount used (e.g., 1234 GB-hours)
- `usage_unit` (String): Unit of measure (e.g., "GB-Hours", "Requests")
- `usage_type` (String): AWS usage type (e.g., "BoxUsage.micro")
- `tags` (Map): Resource tags (e.g., {"Team": "Engineering"})
- `created_at` (String): ISO 8601 timestamp
- `ttl` (Number): Expiration time (Unix epoch) - auto-delete after 90 days

**Indexes:** None needed for our access patterns

### Example Items

```json
{
  "date": "2024-01-15",
  "service_name": "Amazon Elastic Compute Cloud - Compute",
  "cost_usd": 45.23,
  "usage_quantity": 744.0,
  "usage_unit": "Hrs",
  "usage_type": "BoxUsage:t3.medium",
  "tags": {"Team": "Engineering", "Environment": "Production"},
  "created_at": "2024-01-15T08:00:00Z",
  "ttl": 1715875200
}
```

### Access Patterns

```python
# Get all costs for a date
response = table.query(
    KeyConditionExpression=Key('date').eq('2024-01-15')
)

# Get specific service cost for a date
response = table.query(
    KeyConditionExpression=Key('date').eq('2024-01-15') & Key('service_name').eq('EC2')
)
```

### Why This Design?

**Partition Key = date:**
- All services for a day are co-located on same partition
- Fast query for daily summary (most common operation)
- Data distributed across partitions (good for performance)

**Sort Key = service_name:**
- Enables querying single service or all services
- Services returned in alphabetical order (predictable)

**TTL for auto-deletion:**
- DynamoDB automatically deletes items after 90 days
- Saves storage costs
- No Lambda function needed for cleanup

**Tradeoff Accepted:**
- Cannot efficiently query "all EC2 costs for last 30 days"
- Would require 30 queries (one per day)
- But that's fine - we run daily batch jobs, not real-time queries

---

## Table 2: `cost_anomalies`

**Purpose:** Store detected cost spikes and unusual patterns

### Schema

**Primary Key:**
- **Partition Key (PK):** `anomaly_type` (String)
  - Values: "DAILY_SPIKE", "SERVICE_SPIKE", "BUDGET_RISK"
- **Sort Key (SK):** `detection_date` (String, "YYYY-MM-DD")

**Attributes:**
- `anomaly_id` (String): Unique identifier (UUID)
- `service_name` (String): Affected service (if service-specific)
- `actual_cost` (Number): What was spent
- `expected_cost` (Number): What was expected (baseline)
- `percent_increase` (Number): % above baseline (e.g., 45.2)
- `severity` (String): "HIGH" (>50%), "MEDIUM" (20-50%), "LOW" (<20%)
- `details` (String): Human-readable description
- `resolution_status` (String): "NEW", "ACKNOWLEDGED", "RESOLVED"
- `created_at` (String): ISO 8601 timestamp
- `ttl` (Number): Auto-delete after 90 days

### Example Item

```json
{
  "anomaly_type": "SERVICE_SPIKE",
  "detection_date": "2024-01-15",
  "anomaly_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "service_name": "Amazon Elastic Compute Cloud",
  "actual_cost": 145.00,
  "expected_cost": 45.00,
  "percent_increase": 222.2,
  "severity": "HIGH",
  "details": "EC2 costs increased 222% from $45 to $145. Detected 5 new m5.xlarge instances in us-east-1.",
  "resolution_status": "NEW",
  "created_at": "2024-01-15T08:15:23Z",
  "ttl": 1715875200
}
```

### Access Patterns

```python
# Get all anomalies of a type, sorted by date (newest first)
response = table.query(
    KeyConditionExpression=Key('anomaly_type').eq('SERVICE_SPIKE'),
    ScanIndexForward=False  # Reverse order (newest first)
)

# Get anomalies for date range
response = table.query(
    KeyConditionExpression=Key('anomaly_type').eq('SERVICE_SPIKE') & 
                          Key('detection_date').between('2024-01-08', '2024-01-15')
)
```

---

## Table 3: `cost_recommendations`

**Purpose:** Store actionable cost-saving suggestions

### Schema

**Primary Key:**
- **Partition Key (PK):** `recommendation_type` (String)
  - Values: "RIGHT_SIZE", "UNUSED_RESOURCE", "SAVINGS_PLAN", "RESERVED_INSTANCE"
- **Sort Key (SK):** `generated_date` (String, "YYYY-MM-DD")

**Attributes:**
- `recommendation_id` (String): Unique identifier (UUID)
- `resource_id` (String): AWS resource ID
- `resource_arn` (String): Full ARN of resource
- `service_name` (String): AWS service
- `current_cost` (Number): Current monthly cost
- `potential_savings` (Number): Estimated monthly savings
- `savings_percent` (Number): % savings possible
- `recommendation` (String): What action to take
- `priority` (String): "HIGH" (>$100/mo), "MEDIUM" ($25-100), "LOW" (<$25)
- `confidence` (String): "HIGH", "MEDIUM", "LOW"
- `implementation_effort` (String): "LOW", "MEDIUM", "HIGH"
- `status` (String): "NEW", "IN_PROGRESS", "IMPLEMENTED", "REJECTED"
- `details` (Map): Additional context
- `created_at` (String): ISO 8601 timestamp
- `ttl` (Number): Auto-delete after 180 days

### Example Item

```json
{
  "recommendation_type": "UNUSED_RESOURCE",
  "generated_date": "2024-01-15",
  "recommendation_id": "r1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "resource_id": "i-1234567890abcdef0",
  "resource_arn": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0",
  "service_name": "Amazon EC2",
  "current_cost": 50.40,
  "potential_savings": 50.40,
  "savings_percent": 100.0,
  "recommendation": "Stop or terminate unused EC2 instance i-1234567890abcdef0 (t3.medium)",
  "priority": "HIGH",
  "confidence": "HIGH",
  "implementation_effort": "LOW",
  "status": "NEW",
  "details": {
    "instance_type": "t3.medium",
    "availability_zone": "us-east-1a",
    "cpu_avg": 2.3,
    "network_in_avg": 1024,
    "days_unused": 14,
    "reasoning": "CPU utilization <5% for 14 consecutive days."
  },
  "created_at": "2024-01-15T08:30:00Z",
  "ttl": 1731427200
}
```

### Access Patterns

```python
# Get all recommendations of a type
response = table.query(
    KeyConditionExpression=Key('recommendation_type').eq('RIGHT_SIZE'),
    FilterExpression=Attr('status').eq('NEW')  # Only unimplemented
)

# Get high-priority recommendations
response = table.query(
    KeyConditionExpression=Key('recommendation_type').eq('UNUSED_RESOURCE'),
    FilterExpression=Attr('priority').eq('HIGH')
)
```

---

## Cost Calculation

**Monthly storage cost (approximate):**

```
Assumptions:
- 30 days/month
- 20 AWS services tracked
- 5 anomalies/month
- 10 recommendations/month

Storage:
- cost_history: 30 days × 20 services = 600 items × 2 KB = 1.2 MB
- anomalies: 5 items × 1 KB = 5 KB
- recommendations: 10 items × 2 KB = 20 KB
Total: ~1.25 MB

DynamoDB Pricing (US East 1):
- Storage: $0.25 per GB/month
- 1.25 MB = 0.00125 GB × $0.25 = $0.0003/month

Total DynamoDB cost: ~$0.002/month = essentially free
```

---

## Interview Talking Points

### "Why DynamoDB over RDS?"

**Answer:**
"I evaluated three options: DynamoDB, Aurora Serverless, and RDS PostgreSQL.

DynamoDB won because:
- **Cost:** ~$0.25/month vs ~$40/month for Aurora Serverless
- **Access patterns:** Simple key-value lookups (get cost by date+service)
- **Serverless:** No database management, auto-scaling
- **Integration:** Native with Lambda (no VPC complexity)

Tradeoffs I accepted:
- Can't do complex SQL JOIN queries
- Must design schema for specific access patterns upfront
- Less flexible for ad-hoc analysis

When I'd choose RDS instead:
- Complex relational data with many JOINs
- Need ACID transactions across multiple tables
- Team strongly prefers SQL
- Unknown/evolving access patterns

For this use case—time series data with predictable queries—DynamoDB is 160x cheaper with better performance."

### "How did you design the partition key?"

**Answer:**
"I identified my most common access pattern: 'Get all costs for a specific day.'

This led to `date` as partition key because:
- All services for a day are co-located (fast queries)
- Data distributed across partitions (one per day)
- Avoids hot partitions (traffic spread evenly)

I made `service_name` the sort key to enable:
- Get all services for a day: query just by PK
- Get one service for a day: query by PK+SK

Tradeoff: Can't efficiently query 'all EC2 costs across all dates' without multiple queries. But for a daily batch job, that's acceptable—I optimize for the 90% case."
