FROM python:3.9-slim

# Install postgres and mongosql tools
RUN apt-get -y update \
    && apt-get install -y \
        mongo-tools \
        postgresql-client

# Install pipenv
RUN pip install -U pipenv

# Create and set the working directory, so we don't make a mess in the Docker filesystem.
WORKDIR /black-box

# Install project dependencies
COPY Pipfile* ./
RUN pipenv install --system --deploy

# Copy the project files into working directory
COPY . .

# Start the application!
ENTRYPOINT ["sleep"]
CMD ["3000"]