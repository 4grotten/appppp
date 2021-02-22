FROM python:3.9.2-slim as env

ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN apt-get install --no-install-recommends --yes \
    netcat curl git gettext build-essential libpcre3-dev libpq-dev zlib1g-dev libjpeg-dev gdal-bin

WORKDIR /app

COPY ./Pipfile /app/
COPY ./Pipfile.lock /app/
RUN pip install pipenv
RUN pipenv install --system --deploy

COPY . /app/



FROM env as celery

RUN pip install flower


FROM env as development

RUN pipenv install --dev --system --deploy



FROM env as production
# Prod env
ENV DEBUG=False
ENV prometheus_multiproc_dir=/dev/shm

# -------- Building Nginx Unit --------
ARG UNIT_VERSION=1.22.0
RUN curl -O https://unit.nginx.org/download/unit-$UNIT_VERSION.tar.gz && \
    tar xzf unit-$UNIT_VERSION.tar.gz && \
    rm -f unit-$UNIT_VERSION.tar.gz && \
    cd unit-$UNIT_VERSION && \
    ./configure --prefix="/usr" \
            --state="/var/lib/unit" \
            --control="unix:/run/control.unit.sock" \
            --pid="/run/unit.pid" \
            --log="/dev/stdout" \
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
# -------------------------------------

# Unit config
RUN ln -s /app/unit.json /var/lib/unit/conf.json

# Collect static
RUN mv /app/gag.env /app/.env && python manage.py collectstatic --noinput --link && rm /app/.env

# Unit startup
CMD unitd --no-daemon
