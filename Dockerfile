FROM python:3.9-slim

# Install postgres and mongosql tools
RUN apt-get -y update \
    && apt-get install -y \
        mongo-tools \
        postgresql-client

# Copy the project files into working directory
WORKDIR /black-box
COPY . .

ENTRYPOINT ["sleep"]
CMD ["3000"]