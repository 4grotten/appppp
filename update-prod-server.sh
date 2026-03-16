#!/usr/bin/env bash
set -euo pipefail

docker-compose -f docker-compose.production.yml build

docker-compose -f docker-compose.production.yml run --rm django python manage.py collectstatic --noinput

# If column already exists but migration 0197 is not recorded, fake only that migration.
NEEDS_FAKE_0197=$(docker-compose -f docker-compose.production.yml run --rm django python manage.py shell -c '
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

with connection.cursor() as cursor:
	cursor.execute(
		"""
		SELECT 1
		FROM information_schema.columns
		WHERE table_name = %s AND column_name = %s
		LIMIT 1
		""",
		["organizations_regionalpaymentsystemsettings", "conversion_fee_percent"],
	)
	column_exists = cursor.fetchone() is not None

migration_applied = MigrationRecorder(connection).migration_qs.filter(
	app="organizations",
	name="0197_regionalpaymentsystemsettings_conversion_fee_percent",
).exists()

print("yes" if column_exists and not migration_applied else "no")
' | tail -n 1)

if [[ "$NEEDS_FAKE_0197" == "yes" ]]; then
  echo "[deploy] Column exists but 0197 is not applied. Faking organizations 0197 migration."
  docker-compose -f docker-compose.production.yml run --rm django \
	python manage.py migrate organizations 0197_regionalpaymentsystemsettings_conversion_fee_percent --fake --noinput
fi

docker-compose -f docker-compose.production.yml run --rm django python manage.py migrate --noinput

docker-compose -f docker-compose.production.yml up -d --scale celery_worker_subscription=3
docker-compose -f docker-compose-portain.yml up -d
