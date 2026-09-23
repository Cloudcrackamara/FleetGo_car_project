"""Rate limiting for public auth endpoints: sign-in and public endpoints
get 5 attempts per IP per 60 seconds, per the brief's Performance section."""

from fastapi import Depends, HTTPException, Request, status

from app.core.redis_client import redis_client

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 60


def rate_limit(prefix: str):
    """Returns Depends(...) already wrapped — use as
    dependencies=[rate_limit("login")], matching require_role's pattern."""

    def _check(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{prefix}:{ip}"

        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, WINDOW_SECONDS)

        if count > MAX_ATTEMPTS:
            ttl = redis_client.ttl(key)
            retry_after = ttl if ttl and ttl > 0 else WINDOW_SECONDS
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "too many attempts, try again later",
                headers={"Retry-After": str(retry_after)},
            )

    return Depends(_check)