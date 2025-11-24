# CloudCost Guardian - Operations Runbook

## 📋 Table of Contents
- [Daily Operations](#daily-operations)
- [Manual Lambda Triggers](#manual-lambda-triggers)
- [Monitoring & Logs](#monitoring--logs)
- [Data Queries](#data-queries)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## 🔄 Daily Operations

### Automated Schedule
The system runs automatically via EventBridge:
- **08:00 UTC**: Cost Analyzer fetches latest cost data
- **Subsequent runs**: Forecaster, Recommender, and Notifier execute automatically

### Verify Daily Run
```bash
# Check EventBridge rule
aws events describe-rule --name cloudcost-guardian-dev-daily-analysis --region us-east-1

# View recent Lambda executions
aws lambda get-function --function-name cloudcost-guardian-dev-cost-analyzer --region us-east-1
```

---

## 🎯 Manual Lambda Triggers

### Test Individual Functions

#### 1. Cost Analyzer (Fetch Latest Costs)
```bash
aws lambda invoke \
  --function-name cloudcost-guardian-dev-cost-analyzer \
  --region us-east-1 \
  /tmp/analyzer-response.json && cat /tmp/analyzer-response.json | python3 -m json.tool
```

#### 2. Forecaster (Generate Predictions)
```bash
aws lambda invoke \
  --function-name cloudcost-guardian-dev-forecaster \
  --region us-east-1 \
  /tmp/forecaster-response.json && cat /tmp/forecaster-response.json | python3 -m json.tool
```

#### 3. Recommender (Generate Optimization Tips)
```bash
aws lambda invoke \
  --function-name cloudcost-guardian-dev-recommender \
  --region us-east-1 \
  /tmp/recommender-response.json && cat /tmp/recommender-response.json | python3 -m json.tool
```

#### 4. Notifier (Check for Anomalies)
```bash
aws lambda invoke \
  --function-name cloudcost-guardian-dev-notifier \
  --region us-east-1 \
  /tmp/notifier-response.json && cat /tmp/notifier-response.json | python3 -m json.tool
```

### Run Full Pipeline
```bash
# Execute all 4 Lambdas in sequence
for func in cost-analyzer forecaster recommender notifier; do
  echo "🚀 Running $func..."
  aws lambda invoke --function-name cloudcost-guardian-dev-$func --region us-east-1 /tmp/$func.json
  cat /tmp/$func.json | python3 -m json.tool
  echo ""
done
```

---

## 📊 Monitoring & Logs

### View CloudWatch Logs

#### Recent Logs (Last 5 Minutes)
```bash
# Cost Analyzer
aws logs tail /aws/lambda/cloudcost-guardian-dev-cost-analyzer --since 5m --region us-east-1

# Forecaster
aws logs tail /aws/lambda/cloudcost-guardian-dev-forecaster --since 5m --region us-east-1

# Recommender
aws logs tail /aws/lambda/cloudcost-guardian-dev-recommender --since 5m --region us-east-1

# Notifier
aws logs tail /aws/lambda/cloudcost-guardian-dev-notifier --since 5m --region us-east-1
```

#### Follow Logs in Real-Time
```bash
aws logs tail /aws/lambda/cloudcost-guardian-dev-cost-analyzer --follow --region us-east-1
```

#### Search for Errors
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/cloudcost-guardian-dev-cost-analyzer \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --region us-east-1
```

### Lambda Metrics
```bash
# Get Lambda execution metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=cloudcost-guardian-dev-cost-analyzer \
  --start-time $(date -u -d '1 day ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region us-east-1
```

---

## 🗄️ Data Queries

### Query DynamoDB Tables

#### Get Table Item Counts
```bash
echo "📊 Table Statistics:"
for table in cost_history cost_anomalies cost_recommendations; do
  count=$(aws dynamodb scan --table-name $table --select COUNT --region us-east-1 --output json | jq '.Count')
  echo "  • $table: $count items"
done
```

#### View Latest Costs (Today)
```bash
TODAY=$(date -u +%Y-%m-%d)
aws dynamodb query \
  --table-name cost_history \
  --key-condition-expression "#d = :date" \
  --expression-attribute-names '{"#d":"date"}' \
  --expression-attribute-values "{\":date\":{\"S\":\"$TODAY\"}}" \
  --region us-east-1
```

#### View Forecasts
```bash
# Get forecasts for next week
aws dynamodb scan \
  --table-name cost_history \
  --filter-expression "service_name = :sk" \
  --expression-attribute-values '{":sk":{"S":"FORECAST"}}' \
  --limit 7 \
  --region us-east-1
```

#### View Recent Anomalies
```bash
aws dynamodb scan \
  --table-name cost_anomalies \
  --limit 10 \
  --region us-east-1 \
  --output json | jq '.Items'
```

#### View Recommendations
```bash
aws dynamodb scan \
  --table-name cost_recommendations \
  --limit 5 \
  --region us-east-1 \
  --output json | jq '.Items'
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Lambda Function Fails with "Module not found"
**Symptom**: Import errors in CloudWatch Logs

**Solution**:
```bash
# Verify Lambda deployment package
cd terraform
terraform apply -auto-approve
```

#### 2. No Data in DynamoDB Tables
**Symptom**: Queries return empty results

**Solution**:
```bash
# Manually trigger cost analyzer
aws lambda invoke \
  --function-name cloudcost-guardian-dev-cost-analyzer \
  --region us-east-1 \
  /tmp/test.json

# Check logs for errors
aws logs tail /aws/lambda/cloudcost-guardian-dev-cost-analyzer --since 10m --region us-east-1
```

#### 3. Forecaster Returns "DataUnavailableException"
**Symptom**: Forecaster fails with insufficient data error

**Cause**: AWS Cost Explorer forecast API requires at least 3 months of historical data

**Solution**:
- Wait for more cost history to accumulate
- Or use a different AWS account with existing cost data

#### 4. Email Notifications Not Received
**Symptom**: Notifier runs but no emails arrive

**Solution**:
```bash
# Check SNS subscription status
aws sns list-subscriptions-by-topic \
  --topic-arn $(aws sns list-topics --region us-east-1 --output json | jq -r '.Topics[] | select(.TopicArn | contains("cost-alerts")) | .TopicArn') \
  --region us-east-1

# Check if subscription is "PendingConfirmation"
# If yes, check email and click confirmation link
```

#### 5. EventBridge Not Triggering
**Symptom**: Lambdas don't run automatically

**Solution**:
```bash
# Verify EventBridge rule is enabled
aws events describe-rule --name cloudcost-guardian-dev-daily-analysis --region us-east-1

# Check if rule has targets
aws events list-targets-by-rule --rule cloudcost-guardian-dev-daily-analysis --region us-east-1

# Enable rule if disabled
aws events enable-rule --name cloudcost-guardian-dev-daily-analysis --region us-east-1
```

### Debug Mode

Enable verbose logging:
```bash
# Set Lambda environment variable
aws lambda update-function-configuration \
  --function-name cloudcost-guardian-dev-cost-analyzer \
  --environment Variables={LOG_LEVEL=DEBUG} \
  --region us-east-1
```

---

## 🧹 Maintenance

### Clean Up Old Data

#### Remove Expired Records (TTL handles this automatically)
DynamoDB TTL automatically deletes:
- Cost anomalies after 90 days
- Recommendations after 180 days

#### Manual Cleanup (if needed)
```bash
# Delete all forecast records older than 30 days
aws dynamodb scan \
  --table-name cost_history \
  --filter-expression "service_name = :sk AND forecast_generated_at < :ts" \
  --expression-attribute-values '{":sk":{"S":"FORECAST"}, ":ts":{"S":"'$(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%S)'"}}' \
  --region us-east-1 \
  --output json | python3 -c "
import sys, json, boto3
data = json.load(sys.stdin)
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('cost_history')
for item in data['Items']:
    table.delete_item(Key={'date': item['date']['S'], 'service_name': item['service_name']['S']})
print(f'Deleted {len(data[\"Items\"])} old records')
"
```

### Update Lambda Functions
```bash
cd terraform
terraform apply -auto-approve
```

### Backup DynamoDB Tables
```bash
# Enable point-in-time recovery (already enabled by Terraform)
aws dynamodb describe-continuous-backups --table-name cost_history --region us-east-1

# Create on-demand backup
aws dynamodb create-backup \
  --table-name cost_history \
  --backup-name cost-history-backup-$(date +%Y%m%d) \
  --region us-east-1
```

### Cost Optimization
```bash
# View current DynamoDB capacity
aws dynamodb describe-table --table-name cost_history --region us-east-1 | jq '.Table.BillingModeSummary'

# Lambda cost analysis
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '7 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost \
  --filter file://<(echo '{"Dimensions":{"Key":"SERVICE","Values":["AWS Lambda"]}}') \
  --region us-east-1
```

---

## 📞 Support Contacts

- **AWS Support**: https://console.aws.amazon.com/support/
- **GitHub Issues**: [Project Repository Issues]
- **Documentation**: `/docs/` folder in repository

---

## 🔗 Quick Links

- [AWS Lambda Console](https://console.aws.amazon.com/lambda/)
- [DynamoDB Console](https://console.aws.amazon.com/dynamodb/)
- [CloudWatch Logs](https://console.aws.amazon.com/cloudwatch/logs/)
- [Cost Explorer](https://console.aws.amazon.com/cost-management/home#/cost-explorer)
- [EventBridge Console](https://console.aws.amazon.com/events/)

---

**Last Updated**: November 2025
