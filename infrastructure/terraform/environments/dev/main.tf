module "mitrix-tech" {
  source = "../../modules/stack"

  project_id  = "mitrix-tools"
  environment = "dev"
  region      = "europe-west4"
  zone        = "europe-west4-a"
}
