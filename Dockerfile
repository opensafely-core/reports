FROM node:16-buster AS nodeassets
WORKDIR /usr/src/app

COPY assets ./assets
COPY *.js ./
COPY .browserslistrc package-lock.json package.json ./
RUN npm ci && npm run build

# Everything prod is in base as dokku will run without a build target
FROM python:3.9-buster as base

# Don't cache PyPI downloads or wheels.
# Don't use pyc files or __pycache__ folders.
# Don't buffer stdout/stderr output.
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install --no-install-recommends -y sqlite3=3.27.2-3+deb10u1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Do this first to cache them in docker layer so we can skip package
# installation if they haven't changed
WORKDIR /
COPY requirements.txt requirements.dev.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt

WORKDIR /app
COPY . /app
COPY --from=nodeassets /usr/src/app/static/dist ./static/dist

ENV PYTHONPATH=/app

ENTRYPOINT ["/app/entrypoint.sh", "prod"]

FROM base as dev
WORKDIR /
RUN pip install --no-cache-dir --requirement requirements.dev.txt
WORKDIR /app
ENTRYPOINT ["/app/entrypoint.sh", "dev"]

FROM dev as test
WORKDIR /app
ENTRYPOINT ["/app/entrypoint.sh", "test"]
