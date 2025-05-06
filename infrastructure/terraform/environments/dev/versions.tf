terraform {
  backend "gcs" {
    bucket = "company-gcp-tf-state"
    prefix = "terraform/state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.81.0"
    }
  }

  required_version = ">= 1.3.4"
}
