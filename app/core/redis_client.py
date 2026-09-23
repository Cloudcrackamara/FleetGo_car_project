"""One Redis connection, reused everywhere. Redis serves two
unrelated purposes in this app: caching (fleet board) and rate
limiting (login) — both live here, one client, two use-cases."""

import redis

from app.core.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)
