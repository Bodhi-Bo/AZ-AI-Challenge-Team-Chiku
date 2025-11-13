from redis import Redis
from typing import TYPE_CHECKING

from app.config import REDIS_HOST, REDIS_PORT

if TYPE_CHECKING:
    from redis import Redis as RedisType
else:
    RedisType = Redis

redis: RedisType = Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
