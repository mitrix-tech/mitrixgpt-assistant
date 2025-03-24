variable "project_id" {
  description = "The ID of the project in which the resource belongs"
  type        = string
}

variable "environment" {
  description = "Project Environment"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "Deafult GCP region"
  type        = string
  default     = "europe-west4"
}

variable "zone" {
  description = "Deafult GCP zone"
  type        = string
  default     = "europe-west4-a"
}

