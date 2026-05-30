resource "aws_lambda_function" "key_rotation" {
  filename         = "lambda_function.zip"
  function_name    = "${local.name_prefix}-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = filebase64sha256("lambda_function.zip")

  environment {
    variables = {
      ENVIRONMENT         = var.environment
      ENVIRONMENT_SUFFIX  = var.environment_suffix
      NEW_KEY_DESCRIPTION = var.new_key_description
      PARAMETER_PREFIX    = var.parameter_prefix
    }
  }
}