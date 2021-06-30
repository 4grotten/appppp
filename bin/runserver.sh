#!/usr/bin/env bash
set -ex
# This scripts starts default django server
echo "Running django server on 0.0.0.0:8000"
python manage.py runserver 0.0.0.0:8000
