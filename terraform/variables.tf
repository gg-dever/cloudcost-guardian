# ===================================
# INPUT VARIABLES
# ===================================
# These are like function parameters - you can override them when running terraform

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "cloudcost-guardian"
}

variable "alert_email" {
  description = "Email address to receive cost alerts"
  type        = string
  default     = ""  # You'll set this in terraform.tfvars
}

variable "cost_threshold_percent" {
  description = "Percentage increase to trigger anomaly alert"
  type        = number
  default     = 20
}

variable "analysis_schedule" {
  description = "Cron expression for cost analysis (default: daily at 8 AM UTC)"
  type        = string
  default     = "cron(0 8 * * ? *)"
}
