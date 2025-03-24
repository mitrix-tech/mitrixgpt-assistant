module "gcp-network" {
  source  = "terraform-google-modules/network/google"
  version = "~> 7.3.0"

  project_id   = var.project_id
  network_name = local.network_name

  subnets = [
    {
      subnet_name               = local.subnet_name
      subnet_ip                 = "10.0.0.0/17"
      subnet_region             = var.region
      subnet_flow_logs          = true
      subnet_flow_logs_interval = "INTERVAL_15_MIN"
      subnet_flow_logs_sampling = 0.7
      subnet_flow_logs_metadata = "EXCLUDE_ALL_METADATA"
    },
    {
      subnet_name               = local.master_auth_subnetwork
      subnet_ip                 = "10.60.0.0/17"
      subnet_region             = var.region
      subnet_flow_logs          = true
      subnet_flow_logs_interval = "INTERVAL_15_MIN"
      subnet_flow_logs_sampling = 0.7
      subnet_flow_logs_metadata = "EXCLUDE_ALL_METADATA"
    },
  ]

  secondary_ranges = {
    (local.subnet_name) = [
      {
        range_name    = local.pods_range_name
        ip_cidr_range = "192.168.0.0/18"
      },
      {
        range_name    = local.svc_range_name
        ip_cidr_range = "192.168.64.0/18"
      },
    ]
  }

  depends_on = [module.project]
}
