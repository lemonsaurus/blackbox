FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local

# Install uv from the official static binary.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# System tooling needed for backups: postgres-client, mariadb-client,
# mongo-tools, redis-tools.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    redis-tools \
 && rm -rf /var/lib/apt/lists/*

RUN architecture="x86_64"; \
    case $(uname -m) in \
        arm64|aarch64) architecture="arm64" ;; \
    esac; \
    wget -q "https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2004-${architecture}-100.6.1.deb" -O /tmp/mongo-tools.deb && \
    apt-get install -y /tmp/mongo-tools.deb && \
    rm /tmp/mongo-tools.deb && \
    rm -rf /var/lib/apt/lists/*

RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends postgresql-client-16 mariadb-client && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /blackbox

# Install dependencies first (better layer caching), then the project.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

CMD ["blackbox"]
