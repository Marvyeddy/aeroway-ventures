from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
import jwt
from backend.utils.config import Config as cfg

SESSION_TOKEN_EXP = 30 * 60  # 30minutes
REFRESH_TOKEN_EXP = 24 * 2 * 60 * 60  # 2days


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hash: str) -> bool:
    return pwd_context.verify(password, hash)


def create_token(data: dict, token_type: str, expiry: int):
    data_copy = data.copy()

    expiry_period = datetime.now(timezone.utc) + timedelta(seconds=expiry)

    data_copy.update({"type": token_type, "exp": expiry_period})

    return jwt.encode(payload=data_copy, key=cfg.JWT_SECRET_KEY, algorithm=cfg.JWT_ALG)


def create_session_token(data: dict):
    return create_token(data=data, token_type="session", expiry=SESSION_TOKEN_EXP)


def create_refresh_token(data: dict):
    return create_token(data=data, token_type="refresh", expiry=REFRESH_TOKEN_EXP)
