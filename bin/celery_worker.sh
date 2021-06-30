#!/usr/bin/env bash

cat <<"EOF"
    STARTING CELERY WORKER
EOF


set -ex
cd /app
celery celery worker -A project --loglevel=INFO -Q high,default,insta_high,insta_low

