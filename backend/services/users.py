from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.models.users import Users
from backend.schemas.users import UserIn
from backend.utils.security import hash_password


class UserService:
    async def get_user_by_email(self, email: str, session: AsyncSession) -> Users:
        statement = select(Users).where(Users.email == email)

        result = await session.exec(statement)

        return result.first()

    async def get_user_by_id(self, id: str, session: AsyncSession) -> Users:
        statement = select(Users).where(Users.id == id)

        result = await session.exec(statement)

        return result.first()

    async def create_user(self, user_data: UserIn, session: AsyncSession):
        # hash password
        hashed_password = hash_password(user_data.password)

        # create user
        new_user = Users(password=hashed_password, email=user_data.email)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user
