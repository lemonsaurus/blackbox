FROM python:3.9-slim

# Install essential tools
RUN apt-get -y update \
    && apt-get install -y \
        wget \
        gnupg \
        lsb-release

# Install mongotools, used for getting mongo backups
# and redis-tools, used for redis backups.
RUN apt-get install -y mongo-tools redis-tools

# Install the Postgres 12 client, needed for pg_dumpall
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
RUN apt-get -y update \
    && apt-get install -y \
        postgresql-client-12

# Install pipenv
RUN pip install -U pipenv

# Create and set the working directory, so we don't make a mess in the Docker filesystem.
WORKDIR /blackbox

# Install project dependencies
COPY Pipfile* ./
RUN pipenv install --system --deploy

# Copy the project files into working directory
COPY . .

# Start the application!
ENTRYPOINT ["sleep"]
CMD ["300000"]
