#!/usr/bin/env bash

cat <<"EOF"
    STARTING CELERY WORKER
EOF


set -ex
cd /app
celery worker -A project --loglevel=INFO -Q high,default,insta_high,update_login_device,delete_expired_video,delete_expired_posts
