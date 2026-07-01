#!/bin/bash

# LocalStack initialization script
# Creates DynamoDB tables and other AWS resources locally

set -e

echo "🚀 Initializing LocalStack resources..."

# Wait for LocalStack to be ready
echo "⏳ Waiting for LocalStack..."
sleep 5

# Set LocalStack endpoint
export AWS_ENDPOINT_URL="http://localhost:4566"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"

# Create DynamoDB tables
echo "📊 Creating DynamoDB tables..."

# Cost History Table
awslocal dynamodb create-table \
    --table-name cost_history \
    --attribute-definitions \
        AttributeName=PK,AttributeType=S \
        AttributeName=SK,AttributeType=S \
    --key-schema \
        AttributeName=PK,KeyType=HASH \
        AttributeName=SK,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --tags Key=Environment,Value=dev Key=Project,Value=CloudCostGuardian \
    || echo "Table cost_history already exists"

# Cost Anomalies Table
awslocal dynamodb create-table \
    --table-name cost_anomalies \
    --attribute-definitions \
        AttributeName=PK,AttributeType=S \
        AttributeName=SK,AttributeType=S \
    --key-schema \
        AttributeName=PK,KeyType=HASH \
        AttributeName=SK,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --tags Key=Environment,Value=dev Key=Project,Value=CloudCostGuardian \
    || echo "Table cost_anomalies already exists"

# Cost Recommendations Table
awslocal dynamodb create-table \
    --table-name cost_recommendations \
    --attribute-definitions \
        AttributeName=PK,AttributeType=S \
        AttributeName=SK,AttributeType=S \
    --key-schema \
        AttributeName=PK,KeyType=HASH \
        AttributeName=SK,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --tags Key=Environment,Value=dev Key=Project,Value=CloudCostGuardian \
    || echo "Table cost_recommendations already exists"

# Create SNS Topic for alerts
echo "📧 Creating SNS topic..."
awslocal sns create-topic \
    --name cost-alerts \
    || echo "SNS topic already exists"

# Create S3 bucket for logs/data (optional)
echo "🪣 Creating S3 bucket..."
awslocal s3 mb s3://cloudcost-guardian-data || echo "Bucket already exists"

# Seed sample data
echo "🌱 Seeding sample cost data..."
awslocal dynamodb put-item \
    --table-name cost_history \
    --item '{
        "PK": {"S": "SERVICE#EC2"},
        "SK": {"S": "DATE#2026-03-01"},
        "service_name": {"S": "EC2"},
        "date": {"S": "2026-03-01"},
        "cost": {"N": "1250.50"},
        "unit": {"S": "USD"},
        "region": {"S": "us-east-1"},
        "timestamp": {"S": "2026-03-01T00:00:00Z"}
    }' || echo "Sample data already exists"

awslocal dynamodb put-item \
    --table-name cost_history \
    --item '{
        "PK": {"S": "SERVICE#RDS"},
        "SK": {"S": "DATE#2026-03-01"},
        "service_name": {"S": "RDS"},
        "date": {"S": "2026-03-01"},
        "cost": {"N": "850.25"},
        "unit": {"S": "USD"},
        "region": {"S": "us-east-1"},
        "timestamp": {"S": "2026-03-01T00:00:00Z"}
    }' || echo "Sample data already exists"

awslocal dynamodb put-item \
    --table-name cost_history \
    --item '{
        "PK": {"S": "SERVICE#S3"},
        "SK": {"S": "DATE#2026-03-01"},
        "service_name": {"S": "S3"},
        "date": {"S": "2026-03-01"},
        "cost": {"N": "125.75"},
        "unit": {"S": "USD"},
        "region": {"S": "us-east-1"},
        "timestamp": {"S": "2026-03-01T00:00:00Z"}
    }' || echo "Sample data already exists"

echo "✅ LocalStack initialization complete!"
echo ""
echo "📋 Available services:"
echo "  - DynamoDB Tables: cost_history, cost_anomalies, cost_recommendations"
echo "  - SNS Topic: cost-alerts"
echo "  - S3 Bucket: cloudcost-guardian-data"
echo ""
echo "🌐 Access endpoints:"
echo "  - LocalStack: http://localhost:4566"
echo "  - Dashboard: http://localhost:8080"
echo ""
echo "🧪 Test with: awslocal dynamodb scan --table-name cost_history"
