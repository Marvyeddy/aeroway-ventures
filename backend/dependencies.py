from enum import Enum
from typing import Annotated
import uuid
from fastapi import Cookie, Depends, HTTPException, Header, status
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.db.blocklist import token_in_blocklist
from backend.db.database import get_session
from backend.models.users import Users
from backend.utils.security import decode_token
from backend.services.users import UserService

user_service = UserService()


class Role(Enum):
    ADMIN = "admin"
    USER = "user"


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


async def get_current_user_role(current_user: Users = Depends(get_current_user)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not current_user or not getattr(current_user, "role", None):
        raise credentials_exception
    return current_user.role


class RoleChecker:
    def __init__(self, allowed_roles: list[Role]):
        self.allowed_roles = allowed_roles

    def __call__(self, user_role: Role = Depends(get_current_user_role)):
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return user_role
