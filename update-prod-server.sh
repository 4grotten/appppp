#!/usr/bin/env bash
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml run --rm django python manage.py collectstatic --noinput
docker-compose -f docker-compose.production.yml run --rm django python manage.py migrate --noinput
docker-compose -f docker-compose.production.yml up -d

