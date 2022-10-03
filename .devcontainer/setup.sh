#!/bin/bash

python -m pip install --upgrade pip
pip install -r requirements.dev.txt
pip install -r requirements.prod.txt

python manage.py migrate

npm ci
npm run build

python manage.py collectstatic --no-input

# python manage.py runserver localhost:8000
