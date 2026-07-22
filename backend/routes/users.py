from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.db.database import get_session
from backend.schemas.users import UserIn, UserRead
from backend.services.users import UserService
from backend.utils.security import (
    create_refresh_token,
    create_session_token,
    verify_password,
)

user_router = APIRouter()
user_service = UserService()

SESSION_TOKEN_EXP = 30 * 60  # 30minutes
REFRESH_TOKEN_EXP = 24 * 2 * 60 * 60  # 2days


@user_router.post(
    "/create", response_model=UserRead, status_code=status.HTTP_201_CREATED
)
async def signup_user(user_data: UserIn, session: AsyncSession = Depends(get_session)):
    # check is user exists
    user_dict = user_data.model_dump()
    user_exists = await user_service.get_user_by_email(user_dict["email"], session)

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User already exists"
        )

    user = await user_service.create_user(user_data, session)

    return user


@user_router.post("/signin")
async def login_user(user_data: UserIn, session: AsyncSession = Depends(get_session)):
    # check user email if it exists
    user = await user_service.get_user_by_email(user_data.email, session)

    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Credentials"
        )

    data = {"sub": str(user.id), "email": user.email}
    session_token = create_session_token(data)
    refresh_token = create_refresh_token(data)

    response = JSONResponse(
        content={
            "message": "Login successfully",
            "session_token": session_token,
            "refresh_token": refresh_token,
        }
    )

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_TOKEN_EXP,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXP,
    )

    return response
