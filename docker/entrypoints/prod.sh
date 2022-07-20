#!/bin/bash

set -euo pipefail

./manage.py migrate
./manage.py ensure_groups
./manage.py createcachetable

exec gunicorn reports.wsgi --config=gunicorn.conf.py
