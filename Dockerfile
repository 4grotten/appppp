FROM python:3.9-slim as env

ENV PYTHONUNBUFFERED=1
ENV prometheus_multiproc_dir=/dev/shm/prometheus
ENV STATIC_ROOT=/app/static/

RUN apt-get update
RUN apt-get install --no-install-recommends --yes \
    netcat curl git gettext build-essential libpcre3-dev libpq-dev zlib1g-dev libjpeg-dev gdal-bin

WORKDIR /app

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/
RUN pip install pipenv
RUN pipenv lock -r --keep-outdated | pip install -r /dev/stdin && pipenv --rm

COPY . /app/



FROM env as celery

RUN pip install flower


FROM env as development

RUN pipenv lock -r --dev-only --keep-outdated | pip install -r /dev/stdin && pipenv --rm



FROM env as production
ARG UNIT_VERSION=1.21.0
# -------- Building Nginx Unit --------
RUN curl -O https://unit.nginx.org/download/unit-$UNIT_VERSION.tar.gz && \
    tar xzf unit-$UNIT_VERSION.tar.gz && \
    rm -f unit-$UNIT_VERSION.tar.gz && \
    cd unit-$UNIT_VERSION && \
    ./configure --prefix="/usr" \
            --state="/var/lib/unit" \
            --control="unix:/run/control.unit.sock" \
            --pid="/run/unit.pid" \
            --log="/var/log/unit.log" \
            --modules="/usr/lib/unit/modules" \
            --user=unit \
            --group=unit \
            --tests && \
    ./configure python --config=python3-config && \
    make && \
    make tests && \
    ./build/tests && \
    make install && \
    useradd -d /var/lib/unit -U -m -r -s /sbin/nologin unit && \
    rm -rf unit-$UNIT_VERSION

STOPSIGNAL SIGTERM

RUN ln -sf /dev/stdout /var/log/unit.log
# -------------------------------------
