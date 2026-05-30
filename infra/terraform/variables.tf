variable "project_name" {
  description = "Project name used for resource naming and tags."
  type        = string
  default     = "iam-key-rotation"
}

variable "environment" {
  description = "Environment name, for example development, staging, production."
  type        = string
}

variable "environment_suffix" {
  description = "Short environment suffix, for example dv, st, pr."
  type        = string
}

variable "new_key_description" {
  description = "Description for the new access key."
  type        = string
}

variable "parameter_prefix" {
  description = "SSM Parameter Store path prefix."
  type        = string
  default     = "/IAM/Users/"
}

variable "schedule_expression" {
  description = "EventBridge schedule expression."
  type        = string
  default     = "cron(0 10 1 * ? *)"
}