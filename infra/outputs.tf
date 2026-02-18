output "backend_url" {
  description = "Backend Cloud Run service URL"
  value       = google_cloud_run_v2_service.backend.uri
}

output "phoenix_url" {
  description = "Phoenix tracing UI URL"
  value       = google_cloud_run_v2_service.phoenix.uri
}

output "frontend_url" {
  description = "Frontend Cloud Run URL"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "artifact_registry" {
  description = "Artifact Registry URL for backend images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.diveroast.repository_id}"
}

output "phoenix_traces_bucket" {
  description = "GCS bucket for Phoenix trace data"
  value       = google_storage_bucket.phoenix_traces.name
}

output "project_id" {
  description = "GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP region"
  value       = var.region
}
