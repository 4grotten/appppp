#!/usr/bin/env bash

cat <<"EOF"
    STARTING CELERY WORKER
EOF


set -ex
cd /app
celery worker -A project --loglevel=INFO -Q high,default,insta_high,insta_low,update_login_device,delete_expired_video
