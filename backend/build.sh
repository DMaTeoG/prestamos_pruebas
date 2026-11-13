#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install --only-binary :all: -r requirements.txt || pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py train_model || true
python manage.py seed_demo || true
