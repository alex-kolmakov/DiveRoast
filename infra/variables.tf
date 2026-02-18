variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "credentials_file" {
  description = "Path to GCP service account JSON key file"
  type        = string
  default     = "../service.json"
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "gemini_api_key" {
  description = "Gemini API key"
  type        = string
  sensitive   = true
}

variable "gemini_model" {
  description = "Gemini model name"
  type        = string
  default     = "gemini-3-flash-preview"
}

variable "prompt_version" {
  description = "Prompt version (1=roast-master, 2=polite-analyst, 3=dry-humor-analyst)"
  type        = number
  default     = 3
}

variable "backend_image_tag" {
  description = "Tag for the backend Docker image in Artifact Registry"
  type        = string
  default     = "latest"
}

variable "phoenix_image_tag" {
  description = "Tag for the Phoenix Docker image"
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "Tag for the frontend Docker image in Artifact Registry"
  type        = string
  default     = "latest"
}
