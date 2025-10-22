#!/usr/bin/env bash
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml run --rm django python manage.py collectstatic --noinput
docker-compose -f docker-compose.production.yml run --rm django python manage.py migrate --noinput
docker-compose -f docker-compose.production.yml up -d --scale celery_worker_subscription=3
docker-compose -f docker-compose-portain.yml up -d --remove-orphans

