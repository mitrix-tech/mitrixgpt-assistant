locals {
  cluster_type           = "autopilot-private"
  network_name           = "autopilot-private-network"
  subnet_name            = "autopilot-private-subnet"
  master_auth_subnetwork = "autopilot-private-master-subnet"
  pods_range_name        = "ip-range-pods"
  svc_range_name         = "ip-range-svc"
  subnet_names           = [for subnet_self_link in module.gcp-network.subnets_self_links : split("/", subnet_self_link)[length(split("/", subnet_self_link)) - 1]]

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}
