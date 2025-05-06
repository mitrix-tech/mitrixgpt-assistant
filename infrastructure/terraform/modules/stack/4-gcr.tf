resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.region
  repository_id = "companygpt-assistant"
  description   = "Docker repo for companygpt-assistant"
  format        = "DOCKER"
}


resource "google_service_account" "gke_nodes" {
  account_id   = "gke-node-sa"
  display_name = "GKE Node Service Account"
}

resource "google_project_iam_member" "artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.gke_nodes.email}"
}