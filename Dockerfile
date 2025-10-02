FROM python:3.9-slim as env

ARG build_version_report=none

ENV PYTHONUNBUFFERED=1
ENV BACKEND_VERSION_REPORT=${build_version_report}

# Убираем docker-clean, чтобы кеш не удалялся слишком рано
RUN rm -f /etc/apt/apt.conf.d/docker-clean

# Обновляем пакеты
RUN apt-get clean && apt-get update

# Устанавливаем базовые пакеты и компиляторы
RUN apt-get install --no-install-recommends --yes \
    netcat-openbsd \
    curl \
    git \
    gettext \
    python3-dev \
    build-essential \
    libpcre2-dev \
    libpq-dev \
    zlib1g-dev \
    libjpeg-dev && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Устанавливаем графические библиотеки и GDAL
RUN apt-get update && apt-get install --no-install-recommends --yes \
    gdal-bin \
    libgraphviz-dev \
    graphviz \
    libpng-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*


WORKDIR /app
RUN pip3 install setuptools
RUN pip3 install poetry

COPY ./pyproject.toml /app
COPY ./poetry.lock /app

#COPY ./Pipfile /app/
#COPY ./Pipfile.lock /app/
#RUN pip install pipenv
#RUN pipenv install --system --deploy

RUN pip install --upgrade pip
RUN poetry self update
RUN poetry config virtualenvs.create false && \
    poetry install

COPY . /app/
COPY ./bin/gunicorn.sh ./bin/entrypoint.sh ./bin/celery_worker.sh ./bin/runserver.sh /


RUN sed -i 's/\r//' /entrypoint.sh && \
    chmod +x /entrypoint.sh
RUN sed -i 's/\r//' /gunicorn.sh && \
    sed -i 's/\r//' /runserver.sh && \
    sed -i 's/\r//' /celery_worker.sh && \
    chmod +x /gunicorn.sh && \
    chmod +x /runserver.sh && \
    chmod +x /celery_worker.sh

#FROM env as celery-dev
#
#RUN pip install flower
#
#
#FROM env as development
#
#RUN pipenv install --dev --system --deploy

#
#
#FROM env as production
## Prod env
#ENV DEBUG=False
#ENV prometheus_multiproc_dir=/dev/shm
#
## -------- Building Nginx Unit --------
#ARG UNIT_VERSION=1.22.0
#RUN curl -O https://unit.nginx.org/download/unit-$UNIT_VERSION.tar.gz && \
#    tar xzf unit-$UNIT_VERSION.tar.gz && \
#    rm -f unit-$UNIT_VERSION.tar.gz && \
#    cd unit-$UNIT_VERSION && \
#    ./configure --prefix="/usr" \
#            --tmp="/tmp" \
#            --state="/var/lib/unit" \
#            --control="unix:/run/control.unit.sock" \
#            --pid="/run/unit.pid" \
#            --log="/dev/stdout" \
#            --modules="/usr/lib/unit/modules" \
#            --user=unit \
#            --group=unit \
#            --tests && \
#    ./configure python --config=python3-config && \
#    make && \
#    make tests && \
#    ./build/tests && \
#    make install && \
#    useradd -d /var/lib/unit -U -m -r -s /sbin/nologin unit && \
#    rm -rf unit-$UNIT_VERSION
#
#STOPSIGNAL SIGTERM
## -------------------------------------
#
## Unit config
#RUN ln -s /app/unit.json /var/lib/unit/conf.json
#
## Collect static
#RUN mv /app/gag.env /app/.env && python manage.py collectstatic --noinput --link && rm /app/.env
#
## Unit startup
#CMD unitd --no-daemon
