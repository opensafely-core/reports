#!/bin/bash

set -euo pipefail

environment=$1

./manage.py collectstatic --no-input

case $environment in
dev)
  ./manage.py migrate
  ./manage.py ensure_groups
  ./manage.py runserver 0.0.0.0:8000
  ;;
prod)
  ./manage.py migrate
  ./manage.py ensure_groups
  ;;
test)
  pytest --cov=output_explorer --cov=gateway --cov=outputs --cov=tests
  ;;
esac
