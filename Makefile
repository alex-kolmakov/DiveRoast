# DiveRoast GCP Deployment
# Usage:
#   make prepare  — bootstrap infra, build & push Docker images
#   make deploy   — deploy all services to GCP Cloud Run
#   make destroy  — tear down all GCP resources

.PHONY: prepare deploy destroy

prepare:
	@bash scripts/gcp.sh prepare

deploy:
	@bash scripts/gcp.sh deploy

destroy:
	@bash scripts/gcp.sh destroy
