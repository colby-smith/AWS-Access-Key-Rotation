resource "aws_scheduler_schedule" "key_rotation" {
  name                = "${local.name_prefix}-schedule"
  schedule_expression = var.schedule_expression

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.key_rotation.arn
    role_arn = aws_iam_role.eventbridge.arn
  }
}