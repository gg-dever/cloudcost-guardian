# ===================================
# STEP 1: TERRAFORM & PROVIDER SETUP
# ===================================
# This tells Terraform what version to use and which cloud provider

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # Use AWS provider version 5.x
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"  # Needed to zip Lambda code
    }
  }
}

# Configure AWS provider
provider "aws" {
  region = var.aws_region  # Uses variable from variables.tf
  
  # These tags get applied to EVERY resource we create
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      CostCenter  = "FinOps"
    }
  }
}

# ===================================
# DATA SOURCES (Fetch AWS Info)
# ===================================
# These don't create anything - they just fetch info about your AWS account

data "aws_caller_identity" "current" {}  # Gets your AWS account ID
data "aws_region" "current" {}           # Gets current region

# ===================================
# LOCAL VARIABLES (Computed Values)
# ===================================
# These are like "variables" in programming - computed once, used many times

locals {
  account_id  = data.aws_caller_identity.current.account_id
  region      = data.aws_region.current.name
  name_prefix = "${var.project_name}-${var.environment}"  # e.g., "cloudcost-guardian-dev"
  
  # Blueprint table names
  table_names = {
    cost_history      = "cost_history"
    anomalies         = "cost_anomalies"
    recommendations   = "cost_recommendations"
  }
}

# ===================================
# STEP 2: DYNAMODB TABLES
# ===================================
# These store all our cost data, anomalies, and recommendations

# TABLE 1: cost_history
# Stores daily cost breakdown by AWS service
# PK = date (YYYY-MM-DD), SK = service_name
resource "aws_dynamodb_table" "cost_history" {
  name           = local.table_names.cost_history
  billing_mode   = "PAY_PER_REQUEST"  # Only pay for what you use (~$0.0003/month)
  hash_key       = "date"             # Partition Key
  range_key      = "service_name"     # Sort Key
  
  # Define the primary key attributes
  attribute {
    name = "date"
    type = "S"  # S = String
  }
  
  attribute {
    name = "service_name"
    type = "S"
  }
  
  # Enable TTL (Time To Live) - auto-delete after 90 days
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
  
  # Enable point-in-time recovery (backups)
  point_in_time_recovery {
    enabled = true
  }
  
  tags = {
    Name        = "Cost History"
    Description = "Daily cost breakdown by AWS service"
  }
}

# TABLE 2: cost_anomalies
# Stores detected cost spikes and unusual patterns
# PK = anomaly_type (DAILY_SPIKE, SERVICE_SPIKE), SK = detection_date
resource "aws_dynamodb_table" "cost_anomalies" {
  name         = local.table_names.anomalies
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "anomaly_type"      # Partition Key
  range_key    = "detection_date"    # Sort Key
  
  attribute {
    name = "anomaly_type"
    type = "S"
  }
  
  attribute {
    name = "detection_date"
    type = "S"
  }
  
  # TTL for anomalies - 90 days
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
  
  point_in_time_recovery {
    enabled = true
  }
  
  tags = {
    Name        = "Cost Anomalies"
    Description = "Detected cost spikes and unusual patterns"
  }
}

# TABLE 3: cost_recommendations
# Stores actionable cost-saving suggestions
# PK = recommendation_type (RIGHT_SIZE, UNUSED_RESOURCE), SK = generated_date
resource "aws_dynamodb_table" "cost_recommendations" {
  name         = local.table_names.recommendations
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "recommendation_type"  # Partition Key
  range_key    = "generated_date"       # Sort Key
  
  attribute {
    name = "recommendation_type"
    type = "S"
  }
  
  attribute {
    name = "generated_date"
    type = "S"
  }
  
  # TTL for recommendations - 180 days (recommendations age slower)
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
  
  point_in_time_recovery {
    enabled = true
  }
  
  tags = {
    Name        = "Cost Recommendations"
    Description = "Actionable cost-saving suggestions"
  }
}

# ===================================
# STEP 3: IAM ROLE FOR LAMBDA
# ===================================
# Lambda functions need permissions to access DynamoDB, Cost Explorer, SNS, etc.

# IAM Role - Think of this as a "job title" for the Lambda
resource "aws_iam_role" "lambda_execution_role" {
  name = "${local.name_prefix}-lambda-role"

  # Trust policy - allows Lambda service to "assume" this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "Lambda Execution Role"
  }
}

# Policy 1: Basic Lambda execution (CloudWatch Logs)
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Policy 2: DynamoDB access for all tables
resource "aws_iam_role_policy" "lambda_dynamodb_policy" {
  name = "${local.name_prefix}-lambda-dynamodb"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.cost_history.arn,
          aws_dynamodb_table.cost_anomalies.arn,
          aws_dynamodb_table.cost_recommendations.arn
        ]
      }
    ]
  })
}

# Policy 3: Cost Explorer read access (for cost_analyzer)
resource "aws_iam_role_policy" "lambda_cost_explorer_policy" {
  name = "${local.name_prefix}-lambda-cost-explorer"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ce:GetCostAndUsage",
          "ce:GetCostForecast"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy 4: SNS publish access (for notifier)
resource "aws_iam_role_policy" "lambda_sns_policy" {
  name = "${local.name_prefix}-lambda-sns"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = "arn:aws:sns:${local.region}:${local.account_id}:${local.name_prefix}-cost-alerts"
      }
    ]
  })
}

# ===================================
# STEP 4: PACKAGE LAMBDA CODE
# ===================================
# Archive (zip) each Lambda function's code

data "archive_file" "cost_analyzer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src/cost_analyzer"
  output_path = "${path.module}/lambda_packages/cost_analyzer.zip"
}

data "archive_file" "forecaster_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src/forecaster"
  output_path = "${path.module}/lambda_packages/forecaster.zip"
}

data "archive_file" "recommender_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src/recommender"
  output_path = "${path.module}/lambda_packages/recommender.zip"
}

data "archive_file" "notifier_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../src/notifier"
  output_path = "${path.module}/lambda_packages/notifier.zip"
}

# Package ML dependencies as a Lambda Layer (minimal - only NumPy)
data "archive_file" "ml_layer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_layers_minimal"
  output_path = "${path.module}/lambda_packages/ml_layer.zip"
}

# ===================================
# STEP 4B: USE AWS LAMBDA POWERTOOLS LAYER (includes NumPy)
# ===================================
# ===================================
# STEP 5: CREATE LAMBDA FUNCTIONS
# ===================================

# LAMBDA 1: Cost Analyzer
# Fetches daily costs from AWS Cost Explorer
resource "aws_lambda_function" "cost_analyzer" {
  filename         = data.archive_file.cost_analyzer_zip.output_path
  function_name    = "${local.name_prefix}-cost-analyzer"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.cost_analyzer_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = 60  # seconds
  memory_size     = 256 # MB

  environment {
    variables = {
      COST_HISTORY_TABLE = aws_dynamodb_table.cost_history.name
    }
  }

  tags = {
    Name        = "Cost Analyzer"
    Description = "Fetches daily cost data from Cost Explorer"
  }
}

# LAMBDA 2: Forecaster
# Generates 30-day cost predictions using ML
resource "aws_lambda_function" "forecaster" {
  filename         = data.archive_file.forecaster_zip.output_path
  function_name    = "${local.name_prefix}-forecaster"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.forecaster_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = 90
  memory_size     = 256  # Reduced - no ML processing needed

  environment {
    variables = {
      COST_HISTORY_TABLE = aws_dynamodb_table.cost_history.name
      FORECAST_TABLE     = aws_dynamodb_table.cost_history.name
    }
  }

  tags = {
    Name        = "Cost Forecaster"
    Description = "Uses AWS Cost Explorer native forecast API"
  }
}

# LAMBDA 3: Recommender
# Analyzes costs and suggests optimizations
resource "aws_lambda_function" "recommender" {
  filename         = data.archive_file.recommender_zip.output_path
  function_name    = "${local.name_prefix}-recommender"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.recommender_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = 90
  memory_size     = 256

  environment {
    variables = {
      COST_HISTORY_TABLE     = aws_dynamodb_table.cost_history.name
      RECOMMENDATIONS_TABLE  = aws_dynamodb_table.cost_recommendations.name
    }
  }

  tags = {
    Name        = "Cost Recommender"
    Description = "Generates cost optimization recommendations"
  }
}

# LAMBDA 4: Notifier
# Detects anomalies and sends SNS alerts
resource "aws_lambda_function" "notifier" {
  filename         = data.archive_file.notifier_zip.output_path
  function_name    = "${local.name_prefix}-notifier"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "lambda_function.lambda_handler"
  source_code_hash = data.archive_file.notifier_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 256

  environment {
    variables = {
      COST_HISTORY_TABLE    = aws_dynamodb_table.cost_history.name
      ANOMALIES_TABLE       = aws_dynamodb_table.cost_anomalies.name
      SNS_TOPIC_ARN         = aws_sns_topic.cost_alerts.arn
      COST_THRESHOLD_PERCENT = var.cost_threshold_percent
    }
  }

  tags = {
    Name        = "Cost Notifier"
    Description = "Detects anomalies and sends alerts"
  }
}

# ===================================
# STEP 6: SNS TOPIC FOR ALERTS
# ===================================

resource "aws_sns_topic" "cost_alerts" {
  name = "${local.name_prefix}-cost-alerts"

  tags = {
    Name        = "Cost Alerts"
    Description = "Notifications for cost anomalies and spikes"
  }
}

# Email subscription (commented out - add your email address first)
# Email subscription for SNS alerts
# Only created if alert_email variable is provided
resource "aws_sns_topic_subscription" "alert_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.cost_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ===================================
# STEP 7: EVENTBRIDGE SCHEDULER
# ===================================
# Triggers cost_analyzer Lambda daily

resource "aws_cloudwatch_event_rule" "daily_cost_analysis" {
  name                = "${local.name_prefix}-daily-analysis"
  description         = "Trigger cost analysis daily"
  schedule_expression = var.analysis_schedule  # Default: "cron(0 8 * * ? *)" = 8 AM UTC daily

  tags = {
    Name = "Daily Cost Analysis"
  }
}

# Target: Point the rule to cost_analyzer Lambda
resource "aws_cloudwatch_event_target" "cost_analyzer_target" {
  rule      = aws_cloudwatch_event_rule.daily_cost_analysis.name
  target_id = "CostAnalyzerLambda"
  arn       = aws_lambda_function.cost_analyzer.arn
}

# Permission: Allow EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_analyzer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_cost_analysis.arn
}
