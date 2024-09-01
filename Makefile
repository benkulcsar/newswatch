pc:
	pre-commit run -a

test:
	pytest

sv:
	sam validate --lint

sb:
	sam build

setup:
	echo "Local env setup to be added"

deps:
	python -m pip install --upgrade pip; pip install -r src/requirements.txt; pip install -r tests/requirements.txt;

deploy-dev-uk: sv sb
	sam deploy --config-env dev-uk --no-fail-on-empty-changeset;

deploy-dev-us: sv sb
	sam deploy --config-env dev-us --no-fail-on-empty-changeset;

deploy-live-uk: sv sb
	sam deploy --config-env live-uk --no-fail-on-empty-changeset;

deploy-live-us: sv sb
	sam deploy --config-env live-us --no-fail-on-empty-changeset;

check: pc test sv

tf-init-dev:
	terraform -chdir="./terraform" init -reconfigure -backend-config="./backend/backend-dev.tfvars"

tf-init-live:
	terraform -chdir="./terraform" init -reconfigure -backend-config="./backend/backend-live.tfvars"

tf-plan-dev:
	terraform -chdir="./terraform" plan -var-file="./vars/dev.tfvars"

tf-plan-live:
	terraform -chdir="./terraform" plan -var-file="./vars/live.tfvars"
