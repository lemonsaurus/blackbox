FROM redis:latest

COPY ./docker/redis/data.redis /startup/data.redis
COPY ./docker/redis/start-redis.sh /startup/start-redis.sh

CMD ["sh", "/startup/start-redis.sh"]
