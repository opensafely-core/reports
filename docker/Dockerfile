ARG PYTHON_VERSION=3.12
ARG NODE_VERSION=24
ARG UV_VERSION=0.12.0
ARG JUST_VERSION=1.55.0

# Build the frontend assets and Vite manifest.
FROM node:${NODE_VERSION}-trixie-slim AS node-builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY vite.config.mjs ./
COPY assets ./assets
RUN npm run build

FROM ghcr.io/casey/just:${JUST_VERSION} AS just-bin

# Return to the Python runtime image.
FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_VERSION}-trixie-slim AS test
ENV UV_NO_DEV=0

# add in just
COPY --from=just-bin /just /usr/local/bin/

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

# Install the project into `/app`
WORKDIR /app

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Ensure installed tools can be executed out of the box
ENV UV_TOOL_BIN_DIR=/usr/local/bin

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
COPY docker/entrypoints/test.sh /app/docker/entrypoints/test.sh
COPY --from=node-builder /app/assets/dist /app/assets/dist
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Use the non-root user to run our application
# hadolint ignore=DL3066
USER nonroot

# Development image: retain the full source tree and development dependencies.
FROM test AS dev
# hadolint ignore=DL3066
USER nonroot
ENTRYPOINT ["/app/docker/entrypoints/dev.sh"]
CMD ["just", "manage", "runserver", "0.0.0.0:8000"]

# Production image: copy only the runtime application and built assets.
FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_VERSION}-trixie-slim AS prod

COPY --from=just-bin /just /usr/local/bin/
COPY --from=test /app/.venv /app/.venv

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_NO_DEV=1

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project \
 && rm pyproject.toml uv.lock

RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

COPY gateway ./gateway
COPY reports ./reports
COPY services ./services
COPY templates ./templates
COPY static ./static
COPY justfile manage.py gunicorn.conf.py ./
COPY docker/justfile ./docker/justfile
COPY --from=node-builder /app/assets/dist ./assets/dist
COPY docker/entrypoints/prod.sh ./docker/entrypoints/prod.sh

RUN SECRET_KEY=docker-build-placeholder just manage collectstatic --no-input

ENTRYPOINT ["/app/docker/entrypoints/prod.sh"]
# hadolint ignore=DL3066
USER nonroot
