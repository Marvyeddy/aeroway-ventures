import uuid
from pydantic import BaseModel, EmailStr


# register/signup/login
class UserIn(BaseModel):
    email: EmailStr
    password: str


# output data
class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
