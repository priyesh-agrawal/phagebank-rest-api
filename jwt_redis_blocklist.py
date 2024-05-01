import redis
from datetime import timedelta
#sudo apt-get install redis-server
JWT_REDIS_BLOCKLIST = redis.StrictRedis(
    host="localhost", port=6379, db=0, decode_responses=True
)

ACCESS_EXPIRES = timedelta(hours=1)
