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

deploy-dev: sv sb
	sam deploy --config-env dev;

deploy-live: sv sb
	sam deploy --config-env live;

check: pc test sv
