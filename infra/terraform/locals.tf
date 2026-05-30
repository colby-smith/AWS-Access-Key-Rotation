locals {
  name_prefix = "${var.project_name}-${var.environment_suffix}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Repository  = "AWS-Access-Key-Rotation"
  }
}