from typing import Annotated
from amadeus import ClientError, NotFoundError
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from backend.dependencies import get_current_user
from backend.external.flights import amadeus_flight_service
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

flight_router = APIRouter()


@flight_router.post("/shopping/flight-offers", response_model=FlightSearchResponse)
async def search_flights(request: FlightSearchRequestPost):
    try:
        request_body = request.model_dump()

        # TO DO: Search in cache first (REDIS)

        response = amadeus_flight_service.search_flights(request_body)
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flight search failed: {str(e)}")


@flight_router.get("/shopping/flight-offers")
async def search_flights2(request: Annotated[FlightSearchRequestGet, Query(...)]):
    request_body = request.model_dump(exclude_none=True)
    response = amadeus_flight_service.search_flights_get(request_body)
    return response


@flight_router.post(
    "/shopping/flight-offers/pricing", response_model=FlightPricingResponse
)
async def confirm_price(request: FlightOffer):
    try:
        request_body = request.model_dump()
        response = amadeus_flight_service.confirm_price(request_body)
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Price confirmation failed: {str(e)}"
        )


@flight_router.post("/booking/flight-orders")
async def flight_order(
    request: FlightOrderRequestBody, current_user: UserRead = Depends(get_current_user)
):
    """Create order associated with a flight"""
    request_body = request.model_dump(by_alias=True)

    response = amadeus_flight_service.create_flight_order(request_body)
    return response


@flight_router.get("/shopping/seatmaps")
async def view_seat_map_get(flightorderId: Annotated[str, Query()]):
    response = amadeus_flight_service.view_seat_map(flightorderId=flightorderId)
    return response


@flight_router.post("/shopping/seatmaps")
async def view_seat_map_post(request: FlightOffer):
    request_body = request.model_dump()
    response = amadeus_flight_service.view_seat_map_post(request_body)
    return response


@flight_router.get("/booking/flight-orders/{flight_orderId:path}")
async def get_flight_order(
    flight_orderId: Annotated[str, Path()],
    current_user: UserRead = Depends(get_current_user),
):
    """Get flight order details by flight order ID"""
    try:
        response = amadeus_flight_service.get_flight_order(flight_orderId)
        return response
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Flight order not found")
    except Exception:
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
        response = amadeus_flight_service.cancel_flight_order(flight_orderId)
        return response.data
    except ClientError:
        raise HTTPException(status_code=400, detail="Invalid flight order ID")
    except Exception:
        raise HTTPException(
            status_code=500, detail="An error occurred while deleting the flight order"
        )
