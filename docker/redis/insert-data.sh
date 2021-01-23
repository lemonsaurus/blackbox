#!/bin/bash

docker exec -it -e REDISCLI_AUTH=blackbox blackbox-redis redis-cli set foo 100
docker exec -it -e REDISCLI_AUTH=blackbox blackbox-redis redis-cli set bar "baz"
docker exec -it -e REDISCLI_AUTH=blackbox blackbox-redis redis-cli rpush mylist "a" "b" "c"
