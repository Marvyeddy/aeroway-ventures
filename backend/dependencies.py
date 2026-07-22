from typing import Annotated
import uuid
from fastapi import Cookie, Depends, HTTPException, Header, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.db.blocklist import token_in_blocklist
from backend.db.database import get_session
from backend.utils.security import decode_token
from backend.services.users import UserService

user_service = UserService()


async def get_current_user(
    authorization: Annotated[str | None, Header(...)] = None,
    session_token: Annotated[str | None, Cookie(alias="session_token")] = None,
    session: AsyncSession = Depends(get_session),
):
    token = session_token

    if not token and authorization:
        schemes, _, bearer_token = authorization.partition(" ")

        if schemes.lower() == "bearer" and bearer_token:
            token = bearer_token

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token missing.",
        )

    if await token_in_blocklist(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
        )

    token_data = decode_token(token)

    if token_data.get("type") != "session":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired or is invalid.",
        )

    user_id = uuid.UUID(token_data["sub"])

    user = await user_service.get_user_by_id(user_id, session)

    return user
