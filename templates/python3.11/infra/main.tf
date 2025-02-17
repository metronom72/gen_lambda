terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.15"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  lambda_full_name = "${var.project_name}__${var.lambda_name}__${var.environment}"
  bucket_name      = "${var.project_name}"
  archive_path     = "../../${var.lambda_name}.zip"
}

data "aws_s3_bucket" "existing_bucket" {
  bucket = local.bucket_name
}

resource "aws_s3_object" "lambda_code" {
  bucket      = data.aws_s3_bucket.existing_bucket.id
  key         = "${var.environment}/${var.lambda_name}.zip"
  source      = local.archive_path
  source_hash = filebase64sha256(local.archive_path)

  tags = {
    Project     = var.project_name
    Name        = local.lambda_full_name
    Environment = var.environment
  }
}

resource "aws_lambda_function" "lambda_function" {
  function_name    = local.lambda_full_name
  role            = var.lambda_role_arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  s3_bucket       = local.bucket_name
  s3_key          = aws_s3_object.lambda_code.key
  publish         = true
  source_code_hash = filebase64sha256(local.archive_path)

  environment {
    variables = {
      PROJECT     = var.project_name
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Project     = var.project_name
    Name        = local.lambda_full_name
    Environment = var.environment
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [aws_s3_object.lambda_code]
}

resource "aws_lambda_alias" "lambda_alias" {
  name             = "latest"
  function_name    = aws_lambda_function.lambda_function.function_name
  function_version = aws_lambda_function.lambda_function.version
}