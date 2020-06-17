#!/bin/sh

set -o errexit

coverage run --source='.' manage.py test
coverage html