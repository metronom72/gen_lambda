variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g., dev, staging, prod)"
  type        = string
}

variable "lambda_name" {
  description = "Lambda function name"
  type        = string
}

variable "lambda_role_arn" {
  description = "Existing IAM Role ARN for Lambda"
  type        = string
  default     = ""
}

variable "archive_path" {
  description = "Path to archive file"
  type        = string
}

variable "runtime" {
  description = "Identifier of runtime"
  type        = string
}