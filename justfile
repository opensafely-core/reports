# list available commands
default:
    @just --list


# deploy the project
deploy:
	git push dokku main

# configure the local dev env
dev-config:
	cp dotenv-sample .env
	./scripts/dev-env.sh .env

# set up/update the local dev env
setup: pip-install npm-install migrate ensure-superuser ensure-outputs collectstatic

# install correct versions of all Python dependencies
pip-install:
    pip install pip-tools
    pip-sync requirements.txt requirements.dev.txt
    pre-commit install

# install all JS dependencies
npm-install: check-fnm
    fnm use
    npm ci
    npm run build

check-fnm:
    #!/usr/bin/env bash
    if ! which fnm >/dev/null; then
        echo >&2 "You must install fnm. See https://github.com/Schniz/fnm."
        exit 1
    fi

# compile requirements
compile:
    pip-compile --generate-hashes requirements.in
    pip-compile --generate-hashes requirements.dev.in

collectstatic:
    ./manage.py collectstatic --no-input --clear

# run django migrations locally
migrate:
    ./manage.py migrate

# create an admin/admin superuser locally if necessary
ensure-superuser:
    ./manage.py ensure_superuser

# ensure the local app is populated with example outputs
ensure-outputs:
    ./manage.py populate_outputs

# blow away the local database and repopulate it
dev-reset:
    rm db.sqlite3
    just setup

# run the dev server
run:
    python manage.py runserver localhost:8000

# run the test suite and coverage
test:
	python manage.py collectstatic --no-input && \
	pytest --cov=output_explorer --cov=gateway --cov=outputs --cov=tests

# run specific test(s)
test-only TESTPATH:
    pytest {{TESTPATH}}

# run the format checker, sort checker and linter
check:
    #!/bin/bash
    set -e
    echo "Running black, isort and flake8"
    black --check .
    isort --check-only --diff .
    flake8

# run the format checker (black)
format:
    #!/bin/bash
    set -e
    echo "Running black"
    black --check .

# run the linter (flake8)
lint:
    #!/bin/bash
    set -e
    echo "Running flake8"
    flake8

# run the sort checker (isort)
sort:
    #!/bin/bash
    set -e
    echo "Running isort"
    isort --check-only --diff .

# fix formatting and import sort ordering
fix:
    black .
    isort .
