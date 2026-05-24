variable "project_name" {
  description = "Project name for naming infrastructure resources."
  type        = string
  default     = "IAM-Access-Key-Rotation"
}

variable "environment" {
  description = "Deployment environment name used for tagging (e.g. development, staging, production)."
  type        = string
  default     = "production"
}

variable "environment_suffix" {
  description = "Environment suffix for naming resources."
  type        = string
}
