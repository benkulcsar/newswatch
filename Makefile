.PHONY: lint test validate check test-cov badge build

lint:
	uv run pre-commit run -a

test:
	uv run pytest

validate:
	sam validate --lint

check: lint test validate

test-cov:
	uv run pytest --junitxml=pytest.xml --cov=src

badge: test-cov
	uv run coverage-badge -o ./assets/img/coverage.svg

build:
	sam build

setup-local:
	uv sync --dev; uv pip compile pyproject.toml --output-file ./src/requirements.txt

setup-ci:
	uv sync --only-dev

deploy-dev-uk: sv sb
	sam deploy --config-env dev-uk --no-fail-on-empty-changeset;

deploy-dev-us: sv sb
	sam deploy --config-env dev-us --no-fail-on-empty-changeset;

deploy-live-uk: sv sb
	sam deploy --config-env live-uk --no-fail-on-empty-changeset;

deploy-live-us: sv sb
	sam deploy --config-env live-us --no-fail-on-empty-changeset;

tf-init-dev:
	terraform -chdir="./terraform" init -reconfigure -backend-config="./backend/backend-dev.tfvars"

tf-init-live:
	terraform -chdir="./terraform" init -reconfigure -backend-config="./backend/backend-live.tfvars"

tf-plan-dev:
	terraform -chdir="./terraform" plan -var-file="./vars/dev.tfvars"

tf-plan-live:
	terraform -chdir="./terraform" plan -var-file="./vars/live.tfvars"
