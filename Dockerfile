FROM python:3.10 as env

ARG build_version_report=none

ENV PYTHONUNBUFFERED=1
ENV BACKEND_VERSION_REPORT=${build_version_report}
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends --yes \
    netcat-openbsd curl git gettext build-essential libpcre3-dev libpq-dev zlib1g-dev libjpeg-dev gdal-bin graphviz-dev graphviz \
    libjpeg-dev libpng-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY ./pyproject.toml ./poetry.lock /app/

RUN poetry self update
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

COPY . /app/

COPY ./bin/gunicorn.sh ./bin/entrypoint.sh ./bin/celery_worker.sh ./bin/runserver.sh /

RUN sed -i 's/\r//' /entrypoint.sh && chmod +x /entrypoint.sh
RUN sed -i 's/\r//' /gunicorn.sh && sed -i 's/\r//' /runserver.sh && sed -i 's/\r//' /celery_worker.sh && \
    chmod +x /gunicorn.sh /runserver.sh /celery_worker.sh