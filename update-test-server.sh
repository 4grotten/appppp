#!/usr/bin/env bash
docker-compose -f docker-compose.test.yml build
docker-compose -f docker-compose.test.yml run --rm django python manage.py collectstatic --noinput
docker-compose -f docker-compose.test.yml run --rm django python manage.py migrate --noinput
docker-compose -f docker-compose.test.yml up -d
docker-compose -f docker-compose-portainer.yml up -d

