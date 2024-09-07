terraform {
  required_version = "~> 1.9.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.65.0"
    }
    google = {
      version = "~> 6.0.1"
    }
  }
  # bucket and dynamodb_table are stored in backend.tfvars (in gitignore)
  backend "s3" {}
}

provider "aws" {
  region = var.aws_region
}

provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

locals {
  is_live = var.environment == "live" ? true : false
}
