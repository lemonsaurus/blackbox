#!/bin/bash

# Start Redis in background and wait 1 second
redis-server --daemonize yes --requirepass blackbox --appendonly yes && sleep 1

# Add authentication environment variable
export REDISCLI_AUTH="blackbox"

# Insert data to Redis
redis-cli < /startup/data.redis

# Persist data to RDB
redis-cli save

# Shutdown daemonized server
redis-cli shutdown

# Start server normally
redis-server --requirepass blackbox --appendonly yes

