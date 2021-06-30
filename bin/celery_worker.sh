#!/usr/bin/env bash

cat <<"EOF"
    STARTING CELERY WORKER
EOF


set -ex
cd /app
celery -A project worker  -l info
