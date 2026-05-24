locals {
  common_tags = {
    Project     = "IAM-Access-Key-Rotation"
    Application = "Automatic-IAM-Access-Key-Rotation"
    Environment = var.environment
    repository  = "AWS-Access-Key-Rotation"
    ManagedBy   = "terraform"
  }
}
