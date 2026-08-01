from typing import Annotated
from amadeus import ClientError, NotFoundError
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from backend.db.caching import redis_cache
from backend.dependencies import get_current_user
from backend.external.flights import amadeus_flight_service
from backend.models.notifications import NotificationType
from backend.schemas.flight_order import FlightOrderRequestBody
from backend.schemas.flight_search import (
    FlightSearchRequestGet,
    FlightSearchRequestPost,
)
from backend.schemas.flights import (
    FlightOffer,
    FlightPricingResponse,
    FlightSearchResponse,
)
from backend.schemas.users import UserRead
from backend.utils.constants import KafkaEvents, KafkaTopics
from backend.utils.kafka import KafkaProducer
from backend.utils.logger import get_app_logger
from guard_core import SecurityConfig, SecurityDecorator

flight_router = APIRouter()
logger = get_app_logger(__name__)
kafka_producer = KafkaProducer()

config = SecurityConfig()
guard = SecurityDecorator(config)


@flight_router.post("/shopping/flight-offers", response_model=FlightSearchResponse)
@guard.rate_limit(requests=100, window=60)
async def search_flights(request: FlightSearchRequestPost):
    try:
        request_body = request.model_dump()
        logger.info("Flight search requested")
        key = f"flights: {'_'.join(request_body.keys())}"
        flight_data = redis_cache.get(key)

        if flight_data:
            logger.info("Flight search cache hit key=%s", key)
            return flight_data

        response = amadeus_flight_service.search_flights(request_body)
        redis_cache.set(key, response)
        logger.info("Flight search completed key=%s", key)
        return response

    except ValueError as e:
        logger.warning("Flight search validation failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Flight search failed")
        raise HTTPException(status_code=500, detail=f"Flight search failed: {str(e)}")


@flight_router.get("/shopping/flight-offers")
async def search_flights2(request: Annotated[FlightSearchRequestGet, Query(...)]):
    logger.info("Flight search GET requested")
    request_body = request.model_dump(exclude_none=True)
    response = amadeus_flight_service.search_flights_get(request_body)
    logger.info("Flight search GET completed")
    return response


@flight_router.post(
    "/shopping/flight-offers/pricing", response_model=FlightPricingResponse
)
async def confirm_price(request: FlightOffer):
    try:
        logger.info("Flight price confirmation requested")
        request_body = request.model_dump()
        response = amadeus_flight_service.confirm_price(request_body)
        logger.info("Flight price confirmation completed")
        return response

    except ValueError as e:
        logger.warning("Flight price confirmation validation failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Flight price confirmation failed")
        raise HTTPException(
            status_code=500, detail=f"Price confirmation failed: {str(e)}"
        )


@flight_router.post("/booking/flight-orders")
async def flight_order(
    request: FlightOrderRequestBody,
    current_user: UserRead = Depends(get_current_user),
):
    """Create order associated with a flight"""
    logger.info("Flight order creation requested user_id=%s", current_user.id)
    request_body = request.model_dump(by_alias=True)

    response = amadeus_flight_service.create_flight_order(request_body)
    try:
        kafka_producer.start()
        kafka_producer.send(
            KafkaTopics.NOTIFICATION_EVENTS,
            {
                "event_type": KafkaEvents.NOTIFICATION_CREATE,
                "user_id": str(current_user.id),
                "type": NotificationType.BOOKING_CONFIRMED,
                "message": "Your flight booking has been confirmed.",
            },
        )
    except Exception:
        logger.exception("Booking notification failed user_id=%s", current_user.id)
    logger.info("Flight order created user_id=%s", current_user.id)
    return response


@flight_router.get("/shopping/seatmaps")
async def view_seat_map_get(flightorderId: Annotated[str, Query()]):
    logger.info("Seat map GET requested flight_order_id=%s", flightorderId)
    response = amadeus_flight_service.view_seat_map(flightorderId=flightorderId)
    logger.info("Seat map GET completed flight_order_id=%s", flightorderId)
    return response


@flight_router.post("/shopping/seatmaps")
async def view_seat_map_post(request: FlightOffer):
    logger.info("Seat map POST requested")
    request_body = request.model_dump()
    response = amadeus_flight_service.view_seat_map_post(request_body)
    logger.info("Seat map POST completed")
    return response


@flight_router.get("/booking/flight-orders/{flight_orderId:path}")
async def get_flight_order(
    flight_orderId: Annotated[str, Path()],
    current_user: UserRead = Depends(get_current_user),
):
    """Get flight order details by flight order ID"""
    try:
        logger.info(
            "Flight order lookup requested flight_order_id=%s user_id=%s",
            flight_orderId,
            current_user.id,
        )
        response = amadeus_flight_service.get_flight_order(flight_orderId)
        logger.info(
            "Flight order lookup completed flight_order_id=%s user_id=%s",
            flight_orderId,
            current_user.id,
        )
        return response
    except NotFoundError:
        logger.warning("Flight order not found flight_order_id=%s", flight_orderId)
        raise HTTPException(status_code=404, detail="Flight order not found")
    except Exception:
        logger.exception(
            "Flight order lookup failed flight_order_id=%s", flight_orderId
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving the flight order",
        )


@flight_router.delete("/booking/flight-orders/{flight_orderId:path}")
async def cancel_flight_order_management(
    flight_orderId: Annotated[str, Path()],
    current_user: UserRead = Depends(get_current_user),
):
    """Cancel flight order by flight order ID"""
    try:
        logger.info(
            "Flight order cancellation requested flight_order_id=%s user_id=%s",
            flight_orderId,
            current_user.id,
        )
        response = amadeus_flight_service.cancel_flight_order(flight_orderId)
        logger.info(
            "Flight order cancelled flight_order_id=%s user_id=%s",
            flight_orderId,
            current_user.id,
        )
        return response.data
    except ClientError:
        logger.warning(
            "Flight order cancellation rejected flight_order_id=%s", flight_orderId
        )
        raise HTTPException(status_code=400, detail="Invalid flight order ID")
    except Exception:
        logger.exception(
            "Flight order cancellation failed flight_order_id=%s", flight_orderId
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while deleting the flight order"
        )
