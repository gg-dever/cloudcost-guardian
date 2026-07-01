#!/bin/bash

# ===================================
# CloudCost Guardian - One-Click Deployment
# ===================================
# This script deploys the entire CloudCost Guardian system to AWS
# Prerequisites: AWS CLI configured, Terraform installed

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Header
clear
print_header "CloudCost Guardian - One-Click Deployment"
echo ""
echo "This script will deploy the CloudCost Guardian system to AWS."
echo "Estimated deployment time: 5-10 minutes"
echo "Estimated monthly cost: <$3/month"
echo ""

# Step 1: Check Prerequisites
print_header "Step 1: Checking Prerequisites"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install: https://aws.amazon.com/cli/"
    exit 1
fi
print_success "AWS CLI installed"

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    print_error "Terraform not found. Please install: https://www.terraform.io/downloads"
    exit 1
fi
print_success "Terraform installed"

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.11+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_success "Python $PYTHON_VERSION installed"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Run: aws configure"
    exit 1
fi
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
print_success "AWS credentials configured"
echo "   Account: $AWS_ACCOUNT"
echo "   Region: $AWS_REGION"

echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Step 2: Setup Virtual Environment
print_header "Step 2: Setting Up Python Environment"

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists, skipping creation"
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

source venv/bin/activate
print_success "Virtual environment activated"

pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
print_success "Dependencies installed"

# Step 3: Configure Email (Optional)
print_header "Step 3: Configure Email Notifications (Optional)"
echo ""
echo "Would you like to receive email notifications for cost alerts?"
read -p "Enter your email (or press Enter to skip): " ALERT_EMAIL

cd terraform

if [ ! -f "terraform.tfvars" ]; then
    cp terraform.tfvars.example terraform.tfvars 2>/dev/null || touch terraform.tfvars
fi

if [ -n "$ALERT_EMAIL" ]; then
    echo "alert_email = \"$ALERT_EMAIL\"" >> terraform.tfvars
    print_success "Email configured: $ALERT_EMAIL"
else
    print_warning "No email configured - skipping notifications"
fi

# Step 4: Initialize Terraform
print_header "Step 4: Initializing Terraform"

terraform init
print_success "Terraform initialized"

# Step 5: Plan Deployment
print_header "Step 5: Planning Deployment"
echo ""
echo "Terraform will create the following resources:"
echo "  • 3 DynamoDB tables (cost_history, cost_anomalies, cost_recommendations)"
echo "  • 4 Lambda functions (cost-analyzer, forecaster, recommender, notifier)"
echo "  • 1 Lambda layer (shared modules)"
echo "  • 1 SNS topic (cost alerts)"
echo "  • 1 EventBridge rule (daily trigger)"
echo "  • IAM roles and policies"
echo ""

terraform plan -out=tfplan
print_success "Deployment plan created"

echo ""
read -p "Apply this plan? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled. Run terraform apply manually when ready."
    exit 0
fi

# Step 6: Deploy Infrastructure
print_header "Step 6: Deploying Infrastructure"

terraform apply tfplan
print_success "Infrastructure deployed!"

# Step 7: Test Deployment
print_header "Step 7: Testing Deployment"

echo ""
echo "Testing Lambda functions..."

# Test cost analyzer
echo -n "Testing cost-analyzer... "
aws lambda invoke \
    --function-name cloudcost-guardian-dev-cost-analyzer \
    --region $AWS_REGION \
    /tmp/test-analyzer.json &> /dev/null && print_success "OK" || print_error "FAILED"

# Test forecaster
echo -n "Testing forecaster... "
aws lambda invoke \
    --function-name cloudcost-guardian-dev-forecaster \
    --region $AWS_REGION \
    /tmp/test-forecaster.json &> /dev/null && print_success "OK" || print_error "FAILED"

# Test recommender
echo -n "Testing recommender... "
aws lambda invoke \
    --function-name cloudcost-guardian-dev-recommender \
    --region $AWS_REGION \
    /tmp/test-recommender.json &> /dev/null && print_success "OK" || print_error "FAILED"

# Test notifier
echo -n "Testing notifier... "
aws lambda invoke \
    --function-name cloudcost-guardian-dev-notifier \
    --region $AWS_REGION \
    /tmp/test-notifier.json &> /dev/null && print_success "OK" || print_error "FAILED"

# Step 8: Display Results
print_header "Step 8: Deployment Complete! 🎉"

echo ""
echo "CloudCost Guardian is now running in your AWS account!"
echo ""
echo "📊 Resources Created:"
echo "  • Region: $AWS_REGION"
echo "  • Account: $AWS_ACCOUNT"
echo ""

# Get resource details
COST_HISTORY_TABLE=$(aws dynamodb describe-table --table-name cost_history --query 'Table.TableName' --output text 2>/dev/null || echo "cost_history")
ANOMALIES_TABLE=$(aws dynamodb describe-table --table-name cost_anomalies --query 'Table.TableName' --output text 2>/dev/null || echo "cost_anomalies")
RECOMMENDATIONS_TABLE=$(aws dynamodb describe-table --table-name cost_recommendations --query 'Table.TableName' --output text 2>/dev/null || echo "cost_recommendations")

echo "  DynamoDB Tables:"
echo "    • $COST_HISTORY_TABLE"
echo "    • $ANOMALIES_TABLE"
echo "    • $RECOMMENDATIONS_TABLE"
echo ""
echo "  Lambda Functions:"
echo "    • cloudcost-guardian-dev-cost-analyzer"
echo "    • cloudcost-guardian-dev-forecaster"
echo "    • cloudcost-guardian-dev-recommender"
echo "    • cloudcost-guardian-dev-notifier"
echo ""

if [ -n "$ALERT_EMAIL" ]; then
    print_warning "Important: Check your email and confirm the SNS subscription!"
    echo "  Email: $ALERT_EMAIL"
    echo ""
fi

echo "⏰ Automated Schedule:"
echo "  • Cost analysis runs daily at 08:00 UTC"
echo "  • First run will happen tomorrow at 08:00 UTC"
echo ""

echo "💰 Expected Monthly Cost:"
echo "  • Lambda: ~$0.20"
echo "  • DynamoDB: ~$0.50"
echo "  • SNS: ~$0.05"
echo "  • Total: <$3/month"
echo ""

echo "📖 Next Steps:"
echo "  1. Review the deployed resources in AWS Console"
echo "  2. Confirm SNS email subscription (if configured)"
echo "  3. Wait for first automated run (tomorrow 08:00 UTC)"
echo "  4. Or manually trigger now:"
echo "     aws lambda invoke --function-name cloudcost-guardian-dev-cost-analyzer /tmp/test.json"
echo ""

echo "📋 Useful Commands:"
echo "  • View logs: aws logs tail /aws/lambda/cloudcost-guardian-dev-cost-analyzer --follow"
echo "  • Query costs: aws dynamodb scan --table-name cost_history"
echo "  • Destroy: cd terraform && terraform destroy"
echo ""

print_header "Deployment Successful! ✅"

# Save deployment info
cat > ../deployment-info.txt << EOF
CloudCost Guardian Deployment Information
==========================================

Deployment Date: $(date)
AWS Account: $AWS_ACCOUNT
AWS Region: $AWS_REGION
Alert Email: ${ALERT_EMAIL:-Not configured}

DynamoDB Tables:
  - cost_history
  - cost_anomalies
  - cost_recommendations

Lambda Functions:
  - cloudcost-guardian-dev-cost-analyzer
  - cloudcost-guardian-dev-forecaster
  - cloudcost-guardian-dev-recommender
  - cloudcost-guardian-dev-notifier

EventBridge Schedule: Daily at 08:00 UTC

Estimated Monthly Cost: <$3

To destroy: cd terraform && terraform destroy
EOF

print_success "Deployment info saved to deployment-info.txt"

cd ..
