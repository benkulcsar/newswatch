pc:
	pre-commit run -a

test:
	pytest

vs:
	sam validate --lint

setup:
	echo "Local env setup to be added"

deps:
	python -m pip install --upgrade pip; pip install -r src/requirements.txt; pip install -r tests/requirements.txt;

deploy-dev:
	sam build; sam deploy --config-env dev;

deploy-live:
	sam build; sam deploy --config-env live;

check: pc test vs
