FROM python:3.9-slim-bullseye AS env

ARG build_version_report=none

ENV PYTHONUNBUFFERED=1 \
    BACKEND_VERSION_REPORT=${build_version_report} \
    TMPDIR=/tmp \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/opt/poetry/bin:$PATH"

WORKDIR /app

RUN rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get clean && \
    apt-get update && \
    apt-get install --no-install-recommends -y \
        netcat-openbsd \
        curl \
        git \
        gettext \
        python3-dev \
        build-essential \
        libpcre2-dev \
        libpq-dev \
        libffi-dev \
        zlib1g-dev \
        libjpeg-dev \
        libpng-dev \
        gdal-bin \
        graphviz \
        graphviz-dev \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 && \
    rm -rf /var/lib/apt/lists/*

RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock /app/

RUN poetry install --no-root --no-interaction --no-ansi

COPY . /app/
COPY ./bin/gunicorn.sh ./bin/entrypoint.sh ./bin/celery_worker.sh ./bin/runserver.sh /

RUN sed -i 's/\r$//' /entrypoint.sh /gunicorn.sh /runserver.sh /celery_worker.sh && \
    chmod +x /entrypoint.sh /gunicorn.sh /runserver.sh /celery_worker.sh