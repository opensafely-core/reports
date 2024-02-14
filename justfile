# just has no idiom for setting a default value for an environment variable
# so we shell out, as we need VIRTUAL_ENV in the justfile environment
export VIRTUAL_ENV  := `echo ${VIRTUAL_ENV:-.venv}`

# TODO: make it /scripts on windows?
export BIN := VIRTUAL_ENV + "/bin"
export PIP := BIN + "/python -m pip"
# enforce our chosen pip compile flags
export COMPILE := BIN + "/pip-compile --allow-unsafe --generate-hashes"

# Load .env files by default
set dotenv-load := true


# list available commands
default:
    @{{ just_executable() }} --list


# clean up temporary files
clean:
    rm -rf .venv


# ensure valid virtualenv
virtualenv:
    #!/usr/bin/env bash
    set -euo pipefail

    # allow users to specify python version in .env
    PYTHON_VERSION=${PYTHON_VERSION:-python3.12}

    # create venv and upgrade pip
    test -d $VIRTUAL_ENV || { $PYTHON_VERSION -m venv $VIRTUAL_ENV && $PIP install --upgrade pip; }

    # ensure we have pip-tools so we can run pip-compile
    test -e $BIN/pip-compile || $PIP install pip-tools


_compile src dst *args: virtualenv
    #!/usr/bin/env bash
    set -euo pipefail

    # exit if src file is older than dst file (-nt = 'newer than', but we negate with || to avoid error exit code)
    test "${FORCE:-}" = "true" -o {{ src }} -nt {{ dst }} || exit 0
    $BIN/pip-compile --allow-unsafe --generate-hashes --output-file={{ dst }} {{ src }} {{ args }}


# update requirements.prod.txt if requirements.prod.in has changed
requirements-prod *args:
    {{ just_executable() }} _compile requirements.prod.in requirements.prod.txt {{ args }}


# update requirements.dev.txt if requirements.dev.in has changed
requirements-dev *args: requirements-prod
    {{ just_executable() }} _compile requirements.dev.in requirements.dev.txt {{ args }}


# ensure prod requirements installed and up to date
prodenv: requirements-prod
    #!/usr/bin/env bash
    set -euo pipefail

    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.prod.txt -nt $VIRTUAL_ENV/.prod || exit 0

    $PIP install -r requirements.prod.txt
    touch $VIRTUAL_ENV/.prod


_env:
    #!/usr/bin/env bash
    set -euo pipefail

    test -f .env || cp dotenv-sample .env


_dev-config:
    #!/usr/bin/env bash
    set -euo pipefail

    # configure the local dev env
    set -eu
    test -f .dev-configured && exit
    ./scripts/dev-env.sh .env
    touch .dev-configured


# && dependencies are run after the recipe has run. Needs just>=0.9.9. This is
# a killer feature over Makefiles.
#
# ensure dev requirements installed and up to date
devenv: _env prodenv requirements-dev && install-precommit
    #!/usr/bin/env bash
    set -euo pipefail

    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.dev.txt -nt $VIRTUAL_ENV/.dev || exit 0

    $PIP install -r requirements.dev.txt
    touch $VIRTUAL_ENV/.dev


# ensure precommit is installed
install-precommit:
    #!/usr/bin/env bash
    set -euo pipefail

    BASE_DIR=$(git rev-parse --show-toplevel)
    test -f $BASE_DIR/.git/hooks/pre-commit || $BIN/pre-commit install


# upgrade dev or prod dependencies (specify package to upgrade single package, all by default)
upgrade env package="": virtualenv
    #!/usr/bin/env bash
    set -euo pipefail

    opts="--upgrade"
    test -z "{{ package }}" || opts="--upgrade-package {{ package }}"
    FORCE=true {{ just_executable() }} requirements-{{ env }} $opts


# *ARGS is variadic, 0 or more. This allows us to do `just test -k match`, for example.
# Run the tests
test *args: assets
    $BIN/coverage run \
        --branch \
        --source=gateway,reports,services,tests \
        --module pytest \
        {{ args }}
    $BIN/coverage report || $BIN/coverage html


black *args=".": devenv
    $BIN/black --check {{ args }}

ruff *args=".": devenv
    $BIN/ruff check {{ args }}

# run the various dev checks but does not change any files
check: black ruff


# fix formatting and import sort ordering
fix: devenv
    $BIN/black .
    $BIN/ruff --fix .

# setup/update local dev environment
dev-setup: devenv
    $BIN/python manage.py migrate
    $BIN/python manage.py collectstatic --no-input --clear | grep -v '^Deleting '
    # create an admin/admin superuser locally if necessary
    $BIN/python manage.py ensure_superuser
    # ensure the local app is populated with example reports
    INCLUDE_PRIVATE=t $BIN/python manage.py populate_reports
    # ensure the researchers group exists with relevant permissions
    $BIN/python manage.py ensure_groups
    # create the database cache table
    $BIN/python manage.py createcachetable


# Run the dev project
run port="8000": _dev-config assets
    $BIN/python manage.py runserver localhost:{{ port }}


# blow away the local database and repopulate it
dev-reset:
    rm db.sqlite3
    rm http_cache.sqlite
    just dev-setup


# Remove built assets and collected static files
assets-clean:
    rm -rf assets/dist
    rm -rf staticfiles


# Install the Node.js dependencies
assets-install:
    #!/usr/bin/env bash
    set -euo pipefail

    # exit if lock file has not changed since we installed them. -nt == "newer than",
    # but we negate with || to avoid error exit code
    test package-lock.json -nt node_modules/.written || exit 0

    npm ci
    touch node_modules/.written


# Build the Node.js assets
assets-build:
    #!/usr/bin/env bash
    set -euo pipefail

    # find files which are newer than dist/.written in the src directory. grep
    # will exit with 1 if there are no files in the result.  We negate this
    # with || to avoid error exit code
    # we wrap the find in an if in case dist/.written is missing so we don't
    # trigger a failure prematurely
    if test -f assets/dist/.written; then
        find assets/src -type f -newer assets/dist/.written | grep -q . || exit 0
    fi

    npm run build
    touch assets/dist/.written


# Collect the static files
assets-collect: devenv
    #!/usr/bin/env bash
    set -euo pipefail

    # exit if nothing has changed in the built assets since we last collected staticfiles.
    # -nt == "newer than", but we negate with || to avoid error exit code
    test assets/dist/.written -nt staticfiles/.written || exit 0

    $BIN/python manage.py collectstatic --no-input
    touch staticfiles/.written


assets: assets-install assets-build assets-collect

assets-rebuild: assets-clean assets


# build docker image env=dev|prod
docker-build env="dev": _env
    {{ just_executable() }} docker/build {{ env }}


# run tests in docker container
docker-test *args="": _env
    {{ just_executable() }} docker/test {{ args }}


# run dev server in docker container
docker-serve: _env
    {{ just_executable() }} docker/serve


# run cmd in dev docker continer
docker-run *args="bash": _env
    {{ just_executable() }} docker/run {{ args }}


# exec command in an existing dev docker container
docker-exec *args="bash": _env
    {{ just_executable() }} docker/exec {{ args }}
