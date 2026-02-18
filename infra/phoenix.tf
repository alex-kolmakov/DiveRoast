resource "google_storage_bucket" "phoenix_traces" {
  name     = "${var.project_id}-phoenix-traces"
  location = var.region

  uniform_bucket_level_access = true

  depends_on = [google_project_service.apis["storage.googleapis.com"]]
}

resource "google_storage_bucket_iam_member" "phoenix_traces_backend" {
  bucket = google_storage_bucket.phoenix_traces.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_cloud_run_v2_service" "phoenix" {
  name     = "diveroast-phoenix"
  location = var.region

  template {
    service_account       = google_service_account.backend.email
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

    scaling {
      min_instance_count = 1
      max_instance_count = 1
    }

    volumes {
      name = "phoenix-data"
      gcs {
        bucket    = google_storage_bucket.phoenix_traces.name
        read_only = false
      }
    }

    containers {
      image = "arizephoenix/phoenix:${var.phoenix_image_tag}"

      ports {
        container_port = 6006
      }

      env {
        name  = "PHOENIX_WORKING_DIR"
        value = "/data"
      }

      volume_mounts {
        name       = "phoenix-data"
        mount_path = "/data"
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      startup_probe {
        http_get {
          path = "/healthz"
          port = 6006
        }
        initial_delay_seconds = 10
        period_seconds        = 10
        failure_threshold     = 18
      }

      liveness_probe {
        http_get {
          path = "/healthz"
          port = 6006
        }
        period_seconds = 30
      }
    }
  }

  depends_on = [google_project_service.apis["run.googleapis.com"]]
}

# Allow backend service account to invoke Phoenix
resource "google_cloud_run_v2_service_iam_member" "phoenix_backend_invoker" {
  name     = google_cloud_run_v2_service.phoenix.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.backend.email}"
}

# Allow public access to Phoenix UI
resource "google_cloud_run_v2_service_iam_member" "phoenix_public" {
  name     = google_cloud_run_v2_service.phoenix.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
