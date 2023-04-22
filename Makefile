tf-init:
	cd terraform; terraform init -backend-config=backend.tfvars -migrate-state

tf-plan:
	cd terraform; terraform plan

tf-deploy: pre-commit
	cd terraform && terraform apply -auto-approve
