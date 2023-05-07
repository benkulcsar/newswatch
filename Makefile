pc:
	pre-commit run -a

test:
	pytest

check: pc test

setup:
	echo "Local env setup to be added"

install-dependencies:
	python -m pip install --upgrade pip; pip install .[test,extract]; curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

tf-init:
	cd terraform; export TF_CLI_ARGS_init="-backend-config='bucket=${TERRAFORM_NEWSWATCH_S3_BUCKET}' -backend-config='dynamodb_table=${TERRAFORM_NEWSWATCH_DYAMODB_TABLE}'"; terraform init -migrate-state

tf-init-local:
	cd terraform; export TF_CLI_ARGS_init="-backend-config='profile=terraform_newswatch_role' -backend-config='bucket=${TERRAFORM_NEWSWATCH_S3_BUCKET}' -backend-config='dynamodb_table=${TERRAFORM_NEWSWATCH_DYAMODB_TABLE}'"; terraform init -migrate-state

tf-plan:
	cd terraform; terraform plan

tf-apply:
	cd terraform && terraform apply -auto-approve

tf-destroy:
	cd terraform && terraform destroy -auto-approve
