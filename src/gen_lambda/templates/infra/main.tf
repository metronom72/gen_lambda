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
  lambda_full_name = "${substr(var.project_name, 0, 10)}__${substr(var.environment, 0, 4)}__${substr(var.lambda_name, 0, 10)}"
  bucket_name      = var.project_name
  lambda_role_arn = var.lambda_role_arn != "" ? var.lambda_role_arn : aws_iam_role.lambda_role[0].arn
}

data "aws_s3_bucket" "existing_bucket" {
  bucket = local.bucket_name
}

resource "aws_s3_object" "lambda_code" {
  bucket = data.aws_s3_bucket.existing_bucket.id
  key    = "${var.environment}/${var.lambda_name}.zip"
  source = var.archive_path
  etag   = filemd5(var.archive_path)

  tags = {
    Project     = var.project_name
    Name        = local.lambda_full_name
    Environment = var.environment
  }
}

resource "aws_lambda_function" "lambda_function" {
  function_name     = local.lambda_full_name
  role              = local.lambda_role_arn
  handler           = "lambda_function.lambda_handler"
  runtime           = var.runtime
  s3_bucket         = local.bucket_name
  s3_key            = aws_s3_object.lambda_code.key
  publish           = true
  source_code_hash  = filebase64sha256(var.archive_path)
  architectures     = ["arm64"]

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
