from fastapi import FastAPI

from backend.routes.flights import flight_router
from backend.routes.users import user_router

version = "v1"

app = FastAPI(
    title="Aeroway Ventures",
    description="A flight booking API",
    version=version,
    docs_url=f"/api/{version}/docs",
    redoc_url=f"/api/{version}/redoc",
)


@app.get("/")
async def root():
    return {"message": "Hello aeroway ventures!"}


app.include_router(user_router, prefix=f"/api/{version}/users", tags=["users"])
app.include_router(flight_router, prefix=f"/api/{version}/flights", tags=["flights"])
