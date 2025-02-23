resource "aws_iam_role" "lambda_role" {
   count = var.lambda_role_arn == "" ? 1 : 0

  name               = "${substr(var.project_name, 0, 10)}-${substr(var.environment, 0, 4)}-${substr(var.lambda_name, 0, 10)}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = {
    Project     = var.project_name
    Name        = local.lambda_full_name
    Environment = var.environment
  }
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_policy" "lambda_policy" {
  name        = "${substr(var.project_name, 0, 10)}-${substr(var.environment, 0, 4)}-${substr(var.lambda_name, 0, 10)}-lambda-policy"
  description = "IAM policy for Lambda function ${local.lambda_full_name}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.lambda_full_name}:*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "arn:aws:s3:::${local.bucket_name}/${var.environment}/${var.lambda_name}.zip"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logging" {
  role       = aws_iam_role.lambda_role[0].name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_caller_identity" "current" {}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_role[0].arn
}
