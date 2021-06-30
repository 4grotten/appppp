#!/bin/bash
set -ex
cmd="$@"


if [ -z "$POSTGRES_USER" ]; then
    echo "You have not specified POSTGRES_USER. Assuming we are running under docker-compose..."
    export POSTGRES_USER=postgres
fi

if [ -z "$POSTGRES_HOST" ]; then
    echo "You have not specified POSTGRES_HOST. Assuming we are running under docker-compose..."
    export POSTGRES_HOST=postgres
fi
#
#if [ -z "$REDIS_URL" ]; then
#    echo "You have not specified REDIS_URL. Assuming we are running under docker-compose..."
#    export REDIS_URL=redis://redis:6379
#fi

if [ -z "$DATABASE_URL" ]; then
    echo "You have not specified DATABASE_URL. Assuming we are running under docker-compose with default value 5672"
    export DATABASE_URL=postgres://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:5432/$POSTGRES_DB
fi

#export RABBITMQ_USER=$RABBITMQ_DEFAULT_USER
#export RABBITMQ_PASSWORD=$RABBITMQ_DEFAULT_PASS
#export RABBITMQ_VHOST=$RABBITMQ_DEFAULT_VHOST

# if using rabbitmq from host server this parameter is not absent
# if RABBITMQ_HOST == None:
#if [ -z "$RABBITMQ_HOST" ]; then
#    echo "You have not specified RABBITMQ_HOST. Assuming we are running under docker-compose..."
#    export RABBITMQ_HOST=rabbitmq
#fi
#
#if [ -z "$RABBITMQ_PORT" ]; then
#    echo "You have not specified RABBITMQ_PORT. Assuming we are running under docker-compose with default value 5672"
#    export RABBITMQ_PORT=5672
#fi
#
#if [ -z "$RABBITMQ_URL" ]; then
##    echo "You have not specified RABBITMQ_HOST. Assuming we are running under docker-compose..."
##    export RABBITMQ_URL=amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@${RABBITMQ_HOST}:${RABBITMQ_PORT}/${RABBITMQ_VHOST}?heartbeat=600
##    echo "Using composed RABBITMQ_URL=${RABBITMQ_URL}"
#    echo "You should specify RABBITMQ_URL env variable now.."
#    exit 1
#fi


function rabbitmq_ready() {
>&2 python << END
import sys
import pika

rabbitmq_url = '${RABBITMQ_URL}'

#if rabbitmq_url != '':
print('using rabbitmq_url')
conn_params = pika.URLParameters(rabbitmq_url)
try:
    conn = pika.BlockingConnection(conn_params)
    if conn.is_open:
        conn.close()
except pika.exceptions.ConnectionClosed:
    sys.exit(-1)
except pika.exceptions.ProbableAccessDeniedError:
    print('Add RABBITMQ_VHOST to the RABBITMQ_URL')
    raise
else:
    sys.exit(0)
END
}
#
function postgres_ready(){
>&2 python << END
import sys
import psycopg2
try:
#    conn = psycopg2.connect(dbname="$POSTGRES_DB", host="$POSTGRES_HOST",
#                            user="$POSTGRES_USER", password="$POSTGRES_PASSWORD")
    conn = psycopg2.connect('${DATABASE_URL}')
except psycopg2.OperationalError as e:
    print(e)
    sys.exit(-1)
sys.exit(0)
END
}

until postgres_ready; do
  >&2 echo "Postgres is unavailable. Sleeping 5s..."
  >&2 echo "given: '$POSTGRES_HOST', expected  'postgres'"
  >&2 echo "given: '$DATABASE_URL', expected  'postgres'"
  sleep 5
done

>&2 echo "Postgres is up. Continuing..."

until rabbitmq_ready; do
  >&2 echo "RabbitMQ is unavailable. Sleeping 5s..."
  >&2 echo "given: ${RABBITMQ_URL}"
  sleep 5
done

>&2 echo "RabbitMQ is up. Continuing..."
#
#if [ -z "$PYCHARM" ]; then
#    echo "Running without pycharm"
#fi

exec $cmd
