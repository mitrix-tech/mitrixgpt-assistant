module "project" {
  source  = "terraform-google-modules/project-factory/google//modules/project_services"
  version = "~> 14.3"

  project_id                  = var.project_id
  disable_services_on_destroy = false
  activate_apis = [
    "compute.googleapis.com",
    "container.googleapis.com",
    "iam.googleapis.com",
    "storage-component.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "servicenetworking.googleapis.com"
  ]
}

data "google_project" "project" {
  project_id = var.project_id
}
