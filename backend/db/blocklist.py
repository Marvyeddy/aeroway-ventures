import redis.asyncio as aioredis
from backend.utils.config import Config as cfg

SESSION_TOKEN_EXP = 30 * 60  # 30minutes

r = aioredis.from_url(url=cfg.REDIS_URL, decode_responses=True)


async def add_jwt_to_blocklist(jwt: str, expiry: int = SESSION_TOKEN_EXP) -> None:
    return await r.set(name=jwt, value=" ", ex=expiry)


async def token_in_blocklist(jwt: str) -> bool:
    token = await r.get(jwt)

    return token is not None
