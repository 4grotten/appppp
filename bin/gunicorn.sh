#!/usr/bin/env bash
#echo "Collecting static..."
#python manage.py collectstatic --noinput
#
#echo "Collect static is finished."

PORT=8000

cat <<"EOF"
               _.
            ;=',_
           S" .--`
          sS  \__     Gunicorn starting...
       __.' ( \-->
    _=/    _./-\/
   ((\( /-'   -'l
    ) |/ \\
      \\  \
        `~ `~
EOF

>&2 echo "Start"
WORKERS_NUM=$((1 * $(nproc)))
>&2 echo "Workers num: $WORKERS_NUM"

echo "Starting gunicorn"
$(which gunicorn) project.wsgi \
    --workers $WORKERS_NUM \
    --bind 0.0.0.0:$PORT  \
    --chdir=/app \
    --timeout 600 \
    --worker-class gevent \
    --graceful-timeout 300 \
    --max-requests 800 \
    --max-requests-jitter 100 \
    --error-logfile -
