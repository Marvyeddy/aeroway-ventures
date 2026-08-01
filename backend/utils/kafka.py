import json
from typing import Any
from backend.utils.config import Config as cfg
from confluent_kafka import Producer
from backend.utils.logger import get_app_logger

logger = get_app_logger(__name__)


class KafkaProducer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(KafkaProducer, cls).__new__(cls)
            cls._instance.producer = None
            cls._instance.bootstrap_servers = cfg.KAFKA_BOOTSTRAP_SERVERS
        return cls._instance

    def start(self):
        if self.producer:
            return

        conf = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": "fastapi-producer",
        }

        try:
            self.producer = Producer(conf)
            logger.info("Kafka producer initialized on: %s", self.bootstrap_servers)
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            self.producer = None

    def stop(self):
        if self.producer:
            try:
                self.producer.flush(timeout=5.0)
                logger.info("Kafka producer flush completed")
            except Exception as e:
                logger.error(f"Error flushing Kafka producer: {e}")
            finally:
                self.producer = None
                logger.info("Kafka producer stopped")

    @staticmethod
    def _delivery_report(err, msg):
        if err is not None:
            logger.error("Failed to deliver Kafka message: %s", err)
            return

        logger.info(
            "Kafka message delivered to %s [%s] at offset %s",
            msg.topic(),
            msg.partition(),
            msg.offset(),
        )

    def send(self, topic: str, message: dict[str, Any]) -> bool:
        if not self.producer:
            logger.warning("Kafka producer is not initialized. Call start() first.")
            return False

        try:
            self.producer.produce(
                topic,
                value=json.dumps(message).encode("utf-8"),
                callback=self._delivery_report,
            )
            self.producer.poll(0)
            logger.info("Kafka message queued for topic '%s'", topic)
            return True
        except Exception as e:
            logger.error(f"Failed to send message to Kafka topic '{topic}': {e}")
            return False
