from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from config import get_settings


def create_token(user_id: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(hours=settings.access_token_expiry_hours)
    payload = {
        "sub": user_id,
        "exp": expires_at,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verify_token(token: str) -> str | None:
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        subject = payload.get("sub")
        return str(subject) if subject else None
    except JWTError:
        return None
