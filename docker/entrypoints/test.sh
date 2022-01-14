#!/bin/bash

set -euo pipefail

./manage.py collectstatic --no-input
python -m pytest --cov=. --cov-report html --cov-report term-missing:skip-covered
