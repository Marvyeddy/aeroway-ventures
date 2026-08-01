import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.middleware import require_middleware
from backend.routes.flights import flight_router
from backend.routes.notifications import notification_router
from backend.routes.users import user_router
from backend.utils.consumer import create_event_consumer
from backend.utils.kafka import KafkaProducer
from guard.middleware import SecurityMiddleware
from guard_core.models import SecurityConfig
from backend.utils.config import Config as cfg


version = "v1"
event_consumer = create_event_consumer()
kafka_producer = KafkaProducer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    kafka_producer.start()
    event_consumer.start(asyncio.get_running_loop())
    yield
    event_consumer.stop()
    kafka_producer.stop()


app = FastAPI(
    title="Aeroway Ventures",
    description="A flight booking API",
    version=version,
    docs_url=f"/api/{version}/docs",
    redoc_url=f"/api/{version}/redoc",
    lifespan=lifespan,
)

security_config = SecurityConfig(
    rate_limit=100, enable_redis=True, redis_url=cfg.REDIS_URL
)  # Max 100 requests per IP per limit

require_middleware(app)

app.add_middleware(SecurityMiddleware, config=security_config)


@app.get("/")
async def root():
    return {"message": "Hello aeroway ventures!"}


app.include_router(user_router, prefix=f"/api/{version}/users", tags=["users"])
app.include_router(flight_router, prefix=f"/api/{version}/flights", tags=["flights"])
app.include_router(
    notification_router, prefix=f"/api/{version}/notifications", tags=["notifications"]
)
