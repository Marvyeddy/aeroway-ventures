from typing import Annotated
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Cookie,
    Depends,
    HTTPException,
    Header,
    status,
)
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.db.blocklist import add_jwt_to_blocklist, token_in_blocklist
from backend.db.database import get_session
from backend.external.email import send_email
from backend.schemas.users import UserIn, UserRead
from backend.services.users import UserService
from backend.utils.security import (
    create_refresh_token,
    create_session_token,
    decode_token,
    verify_password,
)

user_router = APIRouter()
user_service = UserService()

SESSION_TOKEN_EXP = 30 * 60  # 30minutes
REFRESH_TOKEN_EXP = 24 * 2 * 60 * 60  # 2days


@user_router.post(
    "/create", response_model=UserRead, status_code=status.HTTP_201_CREATED
)
async def signup_user(
    background_tasks: BackgroundTasks,
    user_data: UserIn,
    session: AsyncSession = Depends(get_session),
):
    # check is user exists
    user_dict = user_data.model_dump()
    user_exists = await user_service.get_user_by_email(user_dict["email"], session)

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User already exists"
        )

    user = await user_service.create_user(user_data, session)

    subject = "Welcome to Aeroway Ventures"
    recipients = [user.email]
    body_text = "Thank you for signing up with Aeroway Ventures! We're excited to have you on board."

    background_tasks.add_task(
        send_email,
        subject,
        recipients,
        "welcome.html",
        {
            "subject": subject,
            "body_text": body_text,
            "app_name": "Aeroway Ventures",
        },
    )

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


@user_router.get("/refresh")
async def refresh_token(
    authorization: Annotated[str | None, Header(...)] = None,
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
):
    token = refresh_token

    if not token and authorization:
        schemes, _, bearer_token = authorization.partition(" ")

        if schemes.lower() == "bearer" and bearer_token:
            token = bearer_token

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing.",
        )

    if await token_in_blocklist(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
        )

    token_data = decode_token(token)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired or is invalid.",
        )

    if token_data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )

    user_id = token_data["sub"]
    email = token_data["email"]

    data = {"sub": str(user_id), "email": email}
    session_token = create_session_token(data)
    refresh_token = create_refresh_token(data)

    response = JSONResponse(
        content={
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


@user_router.get("/logout")
async def signout(
    authorization: Annotated[str | None, Header(...)] = None,
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
    session_token: Annotated[str | None, Cookie(alias="session_token")] = None,
):
    tokens_to_revoke: dict[str, int] = {}

    if authorization:
        schemes, _, bearer_token = authorization.partition(" ")

        if schemes.lower() == "bearer" and bearer_token:
            token_data = decode_token(bearer_token)

            if token_data is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired or is invalid.",
                )

            token_type = token_data.get("type")

            if token_type == "session":
                tokens_to_revoke[bearer_token] = SESSION_TOKEN_EXP
            elif token_type == "refresh":
                tokens_to_revoke[bearer_token] = REFRESH_TOKEN_EXP
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type.",
                )

    if session_token:
        tokens_to_revoke[session_token] = SESSION_TOKEN_EXP

    if refresh_token:
        tokens_to_revoke[refresh_token] = REFRESH_TOKEN_EXP

    response = JSONResponse(content={"message": "Logout successfully"})
    response.delete_cookie(key="session_token")
    response.delete_cookie(key="refresh_token")

    for token, expiry in tokens_to_revoke.items():
        await add_jwt_to_blocklist(token, expiry)

    return response
