data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = "https://${module.gke.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gke.ca_certificate)
}

module "gke" {
  source                          = "terraform-google-modules/kubernetes-engine/google//modules/beta-autopilot-private-cluster"
  version                         = "~> 27.0.0"
  project_id                      = var.project_id
  name                            = "mitrix-tools-${var.environment}-cluster"
  regional                        = true
  region                          = var.region
  network                         = module.gcp-network.network_name
  subnetwork                      = local.subnet_names[index(module.gcp-network.subnets_names, local.subnet_name)]
  ip_range_pods                   = local.pods_range_name
  ip_range_services               = local.svc_range_name
  release_channel                 = "REGULAR"
  horizontal_pod_autoscaling      = true
  enable_vertical_pod_autoscaling = true
  enable_private_endpoint         = false
  enable_private_nodes            = true
  master_ipv4_cidr_block          = "172.16.0.0/28"
  network_tags                    = [local.cluster_type]
  cluster_resource_labels         = local.labels

  master_authorized_networks = [
    {
      cidr_block   = "10.60.0.0/17"
      display_name = "VPC"
    },
    {
      cidr_block   = "68.183.121.224/32"
      display_name = "KKovaliov IP"
    },
    {
      cidr_block   = "84.40.220.61/32"
      display_name = "Artur's IP"
    },
    {
      cidr_block   = "46.171.199.75/32"
      display_name = "Office IP"
    }
  ]

  depends_on = [module.project]
}
