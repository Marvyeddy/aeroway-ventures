import asyncio
import inspect
import json
import threading
from concurrent.futures import TimeoutError
from typing import Any, Awaitable, Callable

from confluent_kafka import Consumer, KafkaError
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.db.database import async_engine
from backend.external.email import send_email
from backend.schemas.notifications import NotificationCreate
from backend.services.notification import create_notification
from backend.utils.config import Config as cfg
from backend.utils.constants import KafkaEvents, KafkaTopics
from backend.utils.logger import get_app_logger
from backend.utils.notification_client import publish_notification

logger = get_app_logger(__name__)
EventHandler = Callable[[dict[str, Any]], Awaitable[None] | None]
Session = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


class EventConsumer:
    def __init__(self, group_id: str):
        self.group_id = group_id
        self.bootstrap_servers = cfg.KAFKA_BOOTSTRAP_SERVERS
        self.handlers: dict[str, EventHandler] = {}
        self.consumer: Consumer | None = None
        self.running = False
        self.thread: threading.Thread | None = None
        self.loop: asyncio.AbstractEventLoop | None = None

    def register_handler(self, topic: str, handler: EventHandler) -> None:
        self.handlers[topic] = handler
        logger.info("Registered Kafka handler for topic: %s", topic)

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        if self.running:
            return

        if not self.handlers:
            logger.warning("Kafka consumer was not started because no handlers exist")
            return

        self.loop = loop
        topics = list(self.handlers.keys())

        conf = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }

        try:
            self.consumer = Consumer(conf)
            self.consumer.subscribe(topics)
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            logger.info("Kafka consumer started for topics: %s", topics)
        except Exception as e:
            logger.error("Failed to start Kafka consumer: %s", e)
            self.consumer = None
            self.running = False

    def stop(self) -> None:
        self.running = False

        if self.thread:
            self.thread.join(timeout=5.0)
            self.thread = None

        if self.consumer:
            self.consumer.close()
            self.consumer = None
            logger.info("Kafka consumer stopped")

    async def _execute_handler(
        self, handler: EventHandler, data: dict[str, Any]
    ) -> None:
        result = handler(data)
        if inspect.isawaitable(result):
            await result

    def _run(self) -> None:
        while self.running:
            if self.consumer is None:
                logger.error(
                    "Kafka consumer polling stopped because consumer is missing"
                )
                return

            msg = self.consumer.poll(1.0)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    logger.error("Kafka consumer error: %s", msg.error())
                continue

            topic = msg.topic()
            handler = self.handlers.get(topic)
            if handler is None:
                logger.warning("No Kafka handler registered for topic: %s", topic)
                continue

            try:
                value = msg.value()
                if value is None:
                    logger.warning("Skipping empty Kafka message from topic: %s", topic)
                    self.consumer.commit(msg, asynchronous=False)
                    continue

                data = json.loads(value.decode("utf-8"))

                if self.loop is None or self.loop.is_closed():
                    logger.error(
                        "Skipping Kafka message because event loop is unavailable"
                    )
                    continue

                future = asyncio.run_coroutine_threadsafe(
                    self._execute_handler(handler, data), self.loop
                )
                future.result(timeout=30)
                self.consumer.commit(msg, asynchronous=False)
            except TimeoutError:
                logger.error("Timed out processing Kafka message from topic: %s", topic)
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON Kafka message from topic %s: %s", topic, e)
                self.consumer.commit(msg, asynchronous=False)
            except Exception as e:
                logger.error(
                    "Error processing Kafka message from topic %s: %s", topic, e
                )


async def handle_email_event(event: dict[str, Any]) -> None:
    if event.get("event_type") not in {
        KafkaEvents.EMAIL_SEND,
        KafkaEvents.USER_REGISTERED,
    }:
        logger.warning("Skipping unknown email event type: %s", event.get("event_type"))
        return

    await send_email(
        subject=event["subject"],
        recipients=event["recipients"],
        template_name=event["template_name"],
        template_context=event.get("template_context"),
    )
    logger.info("Welcome email sent for user_id=%s", event.get("user_id"))


async def handle_notification_event(event: dict[str, Any]) -> None:
    event_type = event.get("event_type")
    user_id = event.get("user_id")

    if not user_id:
        logger.warning("Skipping notification event without user_id")
        return

    if event_type == KafkaEvents.NOTIFICATION_CREATE:
        async with Session() as session:
            notification = await create_notification(
                session,
                NotificationCreate(
                    user_id=user_id,
                    type=event["type"],
                    message=event["message"],
                ),
            )

        await publish_notification(
            user_id,
            {
                "event_type": "notification",
                "data": jsonable_encoder(notification),
            },
        )
        logger.info("Notification created and published user_id=%s", user_id)
        return

    if event_type == KafkaEvents.NOTIFICATION_CREATED:
        await publish_notification(
            user_id,
            {
                "event_type": "notification",
                "data": event["data"],
            },
        )
        logger.info("Notification published user_id=%s", user_id)
        return

    if event_type == KafkaEvents.NOTIFICATION_UNREAD_COUNT:
        await publish_notification(
            user_id,
            {
                "event_type": "unread_count",
                "data": event["data"],
            },
        )
        logger.info("Notification unread count published user_id=%s", user_id)
        return

    logger.warning("Skipping unknown notification event type: %s", event_type)


def create_event_consumer() -> EventConsumer:
    consumer = EventConsumer(group_id="aeroway-event-worker")
    consumer.register_handler(KafkaTopics.EMAIL_EVENTS, handle_email_event)
    consumer.register_handler(
        KafkaTopics.NOTIFICATION_EVENTS, handle_notification_event
    )
    return consumer
