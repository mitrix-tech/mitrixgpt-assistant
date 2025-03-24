resource "google_compute_router" "router" {
  project = var.project_id
  name    = "${local.cluster_type}-nat-router"
  network = module.gcp-network.network_name
  region  = var.region
}

module "cloud-nat" {
  source                             = "terraform-google-modules/cloud-nat/google"
  version                            = "~> 4.1"
  project_id                         = var.project_id
  region                             = var.region
  router                             = google_compute_router.router.name
  name                               = "${local.cluster_type}-nat-config"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  depends_on = [module.project]
}
