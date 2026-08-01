import asyncio
import json

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from backend.utils.config import Config as cfg
from backend.utils.logger import get_app_logger

redis = aioredis.from_url(url=cfg.REDIS_URL, decode_responses=True)
logger = get_app_logger(__name__)


async def notification_stream(user_id: str):
    pubsub = redis.pubsub()
    channel = f"notifications:{user_id}"

    await pubsub.subscribe(channel)
    yield 'event: connected\ndata: {"status": "connected"}\n\n'

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message and message["type"] == "message":
                event = json.loads(message["data"])
                yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.01)
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()


async def publish_notification(user_id: str, message: dict) -> None:
    channel = f"notifications:{user_id}"

    try:
        await redis.publish(channel, json.dumps(message))
    except RedisError:
        logger.exception("Failed to publish notification user_id=%s", user_id)
