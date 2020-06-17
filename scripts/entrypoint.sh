#!/bin/sh

set -o errexit

timeout 60 sh -c "until nc -z ${POSTGRES_HOST} ${POSTGRES_PORT}; do sleep 1; done"
python /app/manage.py migrate

export GUNICORN_WORKERS=$((2 * $(nproc) + 1))
exec "$@"
