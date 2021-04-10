FROM python:3.9-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install essential tools
RUN apt-get -y update && apt-get install -y \
    wget \
    gnupg \
    lsb-release

# Install and setup poetry
RUN pip install -U pip \
    && apt install -y curl netcat \
    && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
ENV PATH="${PATH}:/root/.poetry/bin"

# Install mongotools, used for getting mongo backups
# and redis-tools, used for redis backups.
RUN apt-get install -y mongo-tools redis-tools

# Install the Postgres 13 client, needed for pg_dumpall
# And MariaDB client for mysqldump
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN apt-get update -y && \
    apt-get install -y postgresql-client-13 mariadb-client

# Create and set the working directory, so we don't make a mess in the Docker filesystem.
WORKDIR /blackbox

# Copy the project files into working directory
COPY . .

# Run poetry
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# Start the application!
CMD poetry run blackbox
