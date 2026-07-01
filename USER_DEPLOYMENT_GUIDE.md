# 🚀 Deploy CloudCost Guardian to Your AWS Account

## Overview

This guide shows how **anyone** can deploy CloudCost Guardian to their own AWS account to monitor their actual AWS costs.

---

## ✅ What They Need

Before deploying:

- ✅ **AWS Account** with billing access
- ✅ **AWS CLI** installed and configured
- ✅ **Terraform** 1.0+ installed
- ✅ **Python 3.11+** installed
- ✅ **Git** installed
- ✅ **Cost Explorer enabled** (free, but requires 24h activation)

**Time:** 10-15 minutes
**Cost:** <$3/month (AWS Free Tier eligible)

---

## 🎯 Deployment Steps for End Users

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/cloudcost-guardian.git
cd cloudcost-guardian
```

### Step 2: Configure AWS Credentials

They need to configure AWS CLI with their credentials:

```bash
# Option A: Configure interactively
aws configure

# Option B: Use environment variables
export AWS_ACCESS_KEY_ID="their-access-key"
export AWS_SECRET_ACCESS_KEY="their-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Option C: Use AWS profile
export AWS_PROFILE=their-profile-name
```

**Required IAM Permissions:**
- Lambda (create/update/delete functions)
- DynamoDB (create/update/delete tables)
- IAM (create roles and policies)
- EventBridge (create/update/delete rules)
- SNS (create/update/delete topics)
- CloudWatch Logs (create log groups)
- Cost Explorer (read access)

### Step 3: One-Command Deployment

```bash
# Make script executable
chmod +x scripts/quick-deploy.sh

# Run deployment
./scripts/quick-deploy.sh
```

The script will:
1. ✅ Check prerequisites (AWS CLI, Terraform, Python)
2. ✅ Create Python virtual environment
3. ✅ Install dependencies
4. ✅ Ask for their email address (for SNS alerts)
5. ✅ Deploy all infrastructure via Terraform
6. ✅ Test all 4 Lambda functions
7. ✅ Provide deployment summary

### Step 4: Confirm Email Subscription

They'll receive an email from AWS SNS:
- Open email
- Click "Confirm subscription"
- This enables cost alert notifications

### Step 5: Verify Deployment

```bash
# Check Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `cloudcost`)].FunctionName'

# Check DynamoDB tables
aws dynamodb list-tables --query 'TableNames[?contains(@, `cost`)]'

# Check EventBridge rules
aws events list-rules --query 'Rules[?contains(Name, `cloudcost`)].Name'
```

### Step 6: Test Manually (Optional)

```bash
# Trigger cost analyzer manually
aws lambda invoke \
  --function-name cloudcost-guardian-dev-cost-analyzer \
  --region us-east-1 \
  /tmp/test.json

# View result
cat /tmp/test.json

# Check DynamoDB for cost data
aws dynamodb scan --table-name cloudcost-guardian-dev-cost-history --max-items 5
```

---

## 🎛️ Manual Deployment (Alternative)

If they prefer step-by-step control:

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Terraform Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with their preferences
```

**Edit terraform.tfvars:**
```hcl
# Required: Their email for alerts
alert_email = "their-email@example.com"

# Optional: Customize these
environment = "dev"  # or "prod"
aws_region = "us-east-1"  # their preferred region
cost_alert_threshold = 1000.00  # their budget threshold
```

### 3. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Deploy (will ask for confirmation)
terraform apply

# OR deploy without confirmation
terraform apply -auto-approve
```

### 4. Package and Deploy Lambda Functions

```bash
cd ..

# Create Lambda packages
python3 scripts/package-lambdas.py

# Deploy packages (Terraform handles this automatically)
```

---

## 🗑️ Teardown Instructions

When they want to remove CloudCost Guardian from their AWS account:

```bash
cd terraform

# Destroy all resources
terraform destroy

# Verify deletion
aws lambda list-functions | grep cloudcost
aws dynamodb list-tables | grep cost
```

**Important:** This removes:
- All Lambda functions
- All DynamoDB tables (and their data)
- EventBridge rules
- SNS topics
- IAM roles and policies
- CloudWatch log groups

---

## 💰 Cost Breakdown (Their AWS Bill)

Expected monthly costs for their account:

| Service | Usage | Cost |
|---------|-------|------|
| **Lambda** | 4 functions × 30 daily runs | $0.20 |
| **DynamoDB** | ~1000 read/write units | $0.50 |
| **SNS** | 30 notifications | $0.05 |
| **CloudWatch Logs** | 1 GB logs | $0.50 |
| **Cost Explorer API** | Included free | $0.00 |
| **EventBridge** | 30 invocations | $0.00 |
| **TOTAL** | | **~$1.25/month** |

**AWS Free Tier eligible:**
- First 1M Lambda requests/month free
- 25 GB DynamoDB storage free
- 1,000 SNS notifications free

**Note:** Most users who are brand new to AWS will stay under $1/month for the first 12 months.

---

## 🔒 Security Considerations

**For their AWS account:**

### 1. IAM Best Practices
- Use IAM role with least privilege permissions
- Don't share AWS root credentials
- Enable MFA on AWS account
- Regularly rotate access keys

### 2. Data Privacy
- Cost data stays in their AWS account only
- No data leaves their AWS environment
- DynamoDB encryption at rest (enabled by default)
- CloudWatch Logs encrypted

### 3. Cost Explorer Permissions
CloudCost Guardian needs read-only access to Cost Explorer:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 📊 What Gets Deployed to Their Account

### AWS Resources Created:

**4 Lambda Functions:**
1. `cloudcost-guardian-dev-cost-analyzer` - Fetches costs from Cost Explorer
2. `cloudcost-guardian-dev-forecaster` - Generates cost forecasts
3. `cloudcost-guardian-dev-recommender` - Creates optimization recommendations
4. `cloudcost-guardian-dev-notifier` - Sends anomaly alerts

**3 DynamoDB Tables:**
1. `cloudcost-guardian-dev-cost-history` - Stores historical cost data
2. `cloudcost-guardian-dev-cost-anomalies` - Stores detected anomalies
3. `cloudcost-guardian-dev-cost-recommendations` - Stores recommendations

**1 Lambda Layer:**
- `cloudcost-guardian-dev-shared-layer` - Shared code (routers, schemas)

**1 EventBridge Rule:**
- `cloudcost-guardian-dev-daily-schedule` - Triggers daily at 08:00 UTC

**1 SNS Topic:**
- `cloudcost-guardian-dev-cost-alerts` - Email notifications

**4 IAM Roles:**
- One for each Lambda function with specific permissions

**4 CloudWatch Log Groups:**
- One for each Lambda function

---

## 🧪 Testing After Deployment

They can verify it's working:

### 1. Check Lambda Logs

```bash
# View cost analyzer logs
aws logs tail /aws/lambda/cloudcost-guardian-dev-cost-analyzer --follow
```

### 2. Query Cost Data

```bash
# Check if cost data is being collected
aws dynamodb scan \
  --table-name cloudcost-guardian-dev-cost-history \
  --max-items 10
```

### 3. Trigger Manually

```bash
# Force a run without waiting for schedule
aws lambda invoke \
  --function-name cloudcost-guardian-dev-cost-analyzer \
  /tmp/output.json \
  --log-type Tail \
  --query 'LogResult' \
  --output text | base64 -d
```

### 4. Check for Anomalies

```bash
# View detected anomalies
aws dynamodb scan \
  --table-name cloudcost-guardian-dev-cost-anomalies
```

---

## 🎯 Customization Options

They can customize CloudCost Guardian for their needs:

### 1. Change Schedule

Edit `terraform/main.tf`:
```hcl
resource "aws_cloudwatch_event_rule" "cost_analyzer_schedule" {
  schedule_expression = "cron(0 8 * * ? *)"  # Change to their preferred time
}
```

### 2. Adjust Alert Threshold

Edit `terraform/terraform.tfvars`:
```hcl
cost_alert_threshold = 500.00  # Their budget limit
```

### 3. Change Data Retention

Edit Lambda environment variables:
```hcl
environment_variables = {
  RETENTION_DAYS = "90"  # Change retention period
}
```

### 4. Add More Services to Monitor

Edit `src/cost_analyzer/lambda_cost_analyzer.py`:
```python
# Add specific services to focus on
services_to_monitor = [
    "AmazonEC2",
    "AmazonRDS",
    "AmazonS3",
    "AWSLambda",
    "AmazonDynamoDB"
]
```

---

## ❓ Troubleshooting

### Issue: "Cost Explorer is not enabled"
**Solution:**
```bash
# Cost Explorer requires 24h to activate
# Enable in AWS Console: Billing → Cost Explorer
# Wait 24 hours, then re-run deployment
```

### Issue: "Insufficient permissions"
**Solution:**
```bash
# User needs these IAM permissions:
# - Lambda full access
# - DynamoDB full access
# - IAM role creation
# - Cost Explorer read access

# Attach AWS managed policy: PowerUserAccess
# OR create custom policy with required permissions
```

### Issue: "No cost data appearing"
**Solution:**
```bash
# Wait 24-48 hours for Cost Explorer to populate
# Check Lambda logs for errors:
aws logs tail /aws/lambda/cloudcost-guardian-dev-cost-analyzer --since 1h
```

### Issue: "Not receiving email alerts"
**Solution:**
```bash
# Check SNS subscription status:
aws sns list-subscriptions-by-topic \
  --topic-arn $(aws sns list-topics --query 'Topics[?contains(TopicArn, `cost-alerts`)].TopicArn' --output text)

# Resend confirmation email:
aws sns subscribe \
  --topic-arn TOPIC_ARN \
  --protocol email \
  --notification-endpoint their-email@example.com
```

---

## 📖 Additional Documentation

For the end user:

- **Operations Guide:** [docs/OPERATIONS.md](docs/OPERATIONS.md) - Daily operations
- **Security Guide:** [docs/SECURITY.md](docs/SECURITY.md) - Security best practices
- **Data Model:** [docs/data-model.md](docs/data-model.md) - DynamoDB schema
- **Architecture:** [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) - System design

---

## 🆘 Getting Help

If they encounter issues:

1. **Check logs:**
   ```bash
   aws logs tail /aws/lambda/cloudcost-guardian-dev-cost-analyzer --follow
   ```

2. **Review Terraform output:**
   ```bash
   terraform show
   ```

3. **Open GitHub Issue:**
   - Go to: https://github.com/YOUR_USERNAME/cloudcost-guardian/issues
   - Provide: Error message, AWS region, Terraform version

4. **Contact maintainer:**
   - LinkedIn: [Your LinkedIn URL]
   - Email: [Your email if you want to provide it]

---

## ✅ Post-Deployment Checklist

After deployment, they should:

- [ ] Confirm SNS email subscription
- [ ] Verify Lambda functions are deployed
- [ ] Check DynamoDB tables exist
- [ ] Test cost analyzer manually
- [ ] Review first cost data (may take 24h)
- [ ] Set up billing alerts in AWS console (backup)
- [ ] Review CloudWatch logs for errors
- [ ] Bookmark CloudCost Guardian dashboard (if deployed)
- [ ] Document their terraform.tfvars settings
- [ ] Save deployment outputs

---

## 🎯 What They'll See

**Within 24-48 hours:**
- Cost data from their AWS account in DynamoDB
- Daily automated runs via EventBridge
- Email notifications if anomalies detected
- Cost forecasts for next 30 days
- Optimization recommendations

**Example email alert:**
```
Subject: CloudCost Guardian - Cost Anomaly Detected

Service: AmazonEC2
Date: 2026-03-29
Anomaly Type: SPIKE
Expected Cost: $150.00
Actual Cost: $450.00
Increase: 200%

Details: Detected unusual cost increase for AmazonEC2.
Recommendation: Review EC2 instance usage and consider right-sizing.

View details: [Link to DynamoDB query or dashboard]
```

---

**They're ready to deploy!** 🚀

The key is that they:
1. Clone your GitHub repo
2. Configure their AWS credentials
3. Run `./scripts/quick-deploy.sh`
4. Confirm email subscription
5. Wait 24-48h for cost data to populate

That's it! CloudCost Guardian will start monitoring their AWS costs automatically.
