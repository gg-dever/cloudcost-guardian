# ===================================
# TERRAFORM OUTPUTS
# ===================================
# These values are shown after "terraform apply"

# DynamoDB Tables
output "cost_history_table_name" {
  description = "Name of the cost history DynamoDB table"
  value       = aws_dynamodb_table.cost_history.name
}

output "cost_anomalies_table_name" {
  description = "Name of the cost anomalies DynamoDB table"
  value       = aws_dynamodb_table.cost_anomalies.name
}

output "cost_recommendations_table_name" {
  description = "Name of the cost recommendations DynamoDB table"
  value       = aws_dynamodb_table.cost_recommendations.name
}

# Lambda Functions
output "lambda_functions" {
  description = "ARNs of all Lambda functions"
  value = {
    cost_analyzer = aws_lambda_function.cost_analyzer.arn
    forecaster    = aws_lambda_function.forecaster.arn
    recommender   = aws_lambda_function.recommender.arn
    notifier      = aws_lambda_function.notifier.arn
  }
}

# SNS Topic
output "sns_topic_arn" {
  description = "ARN of the SNS topic for cost alerts"
  value       = aws_sns_topic.cost_alerts.arn
}

# EventBridge Rule
output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule for daily analysis"
  value       = aws_cloudwatch_event_rule.daily_cost_analysis.name
}

# Quick reference
output "summary" {
  description = "Summary of deployed resources"
  value = {
    tables_created         = 3
    lambda_functions       = 4
    eventbridge_rules      = 1
    sns_topics            = 1
    iam_roles             = 1
    schedule              = var.analysis_schedule
    alert_email           = var.alert_email
    cost_threshold        = "${var.cost_threshold_percent}%"
  }
}
