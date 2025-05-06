module "company-tech" {
  source = "../../modules/stack"

  project_id  = "company-tools"
  environment = "dev"
  region      = "europe-west4"
  zone        = "europe-west4-a"
}
