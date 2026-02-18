resource "google_artifact_registry_repository" "diveroast" {
  location      = var.region
  repository_id = "diveroast"
  format        = "DOCKER"
  description   = "DiveRoast Docker images"

  depends_on = [google_project_service.apis["artifactregistry.googleapis.com"]]
}
