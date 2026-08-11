set minimum-version := '1.55.0'

# Load .env files by default
set dotenv-load

# Run `just` to list the available recipes
set default-list

# Enable Docker just recipes to run with `just docker [command]`
mod docker

# Ensure prod dependencies are installed and up to date
[group('dependencies')]
prod-env:
    uv sync --frozen --no-dev

copy-sample-env-file:
    #!/usr/bin/env bash
    set -euo pipefail

    test -f .env || cp dotenv-sample .env

setup-dev-env-file: copy-sample-env-file
    #!/usr/bin/env bash
    set -euo pipefail

    # configure the local dev env
    set -eu
    test -f .dev-configured && exit
    ./scripts/dev-env.sh .env
    touch .dev-configured

# ensure dev requirements installed and up to date
devenv: copy-sample-env-file
    uv sync --frozen
    uv run pre-commit install

# upgrade dev or prod dependencies (specify package to upgrade single package, all by default)
upgrade env package="":
    #!/usr/bin/env bash
    set -euo pipefail

    if [ -n '{{ package }}' ]; then
        uv lock --upgrade-package '{{ package }}'
    else
        uv lock --upgrade
    fi
    uv sync

# Upgrade all dev and prod dependencies.
# This is the default input command to update-dependencies action
# https://github.com/bennettoxford/update-dependencies-action
update-dependencies:
    just upgrade prod
    just upgrade dev

# *ARGS is variadic, 0 or more. This allows us to do `just test -k match`, for example.
# Run the tests
test *args: assets
    uv run coverage run \
        --branch \
        --source=gateway,reports,services,tests \
        --module pytest \
        {{ args }}
    uv run coverage report

[group('ruff')]
format *args=".":
    uv run ruff format --check {{ args }}

[group('ruff')]
lint *args=".":
    uv run ruff check --output-format=full {{ args }}

# run the various dev checks but does not change any files
[group('ruff')]
check: format lint

# fix formatting and import sort ordering
[group('ruff')]
fix:
    uv run ruff check --fix .
    uv run ruff format .

manage command *args:
    uv run manage.py {{command}} {{args}}

prod-server:
    uv run gunicorn reports.wsgi --config=gunicorn.conf.py

# setup/update local dev environment
dev-setup:
    just manage migrate
    just assets-collect

    # create an admin/admin superuser locally if necessary
    just manage ensure_superuser

    # ensure the local app is populated with example reports
    INCLUDE_PRIVATE=t just manage populate_reports

    # ensure the researchers group exists with relevant permissions
    just manage ensure_groups

    # create the database cache table
    just manage createcachetable

# Run the dev project
run port="8000": setup-dev-env-file assets
    just manage runserver localhost:{{ port }}

# blow away the local database and repopulate it
dev-reset:
    rm db.sqlite3
    rm http_cache.sqlite
    just dev-setup

# Initial set up of assets files
[group('assets')]
assets: assets-install assets-build assets-collect

# Build the Node.js assets
[group('assets')]
assets-build:
    npm run build

# Remove built assets and collected static files
[group('assets')]
assets-clean:
    rm -rf assets/dist
    rm -rf staticfiles

# Collect the static files
[group('assets')]
assets-collect:
    just manage collectstatic --no-input

# Install the Node.js dependencies
[group('assets')]
assets-install:
    npm ci

# Remove existing assets and static files, then rebuild from scratch
[group('assets')]
assets-rebuild: assets-clean assets
