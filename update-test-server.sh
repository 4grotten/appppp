#!/usr/bin/env bash
set -euo pipefail

docker-compose -f docker-compose.test.yml build

docker-compose -f docker-compose.test.yml run --rm django python manage.py collectstatic --noinput
docker-compose -f docker-compose.test.yml run --rm django python manage.py migrate --noinput

docker-compose -f docker-compose.test.yml up -d --scale celery_worker_subscription=3
docker-compose -f docker-compose-portain.yml up -d
