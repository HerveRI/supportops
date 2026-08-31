from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.config import settings

JWT_ALGOTITHM = "HS256"

password_hash = PasswordHash.recommended()

# Used when a login attempt references an email that does not exist.
# Performing a real password verification helps reduce timing differences
# between existing and nonexistent accounts.
DUMMY_PASSWORD_HASH = password_hash.hash("supportops-dummy-password")


def hash_password(password: str) -> str:
    """Hash a plaintext password for storate."""

    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Check whether a plaintext password mateches a stored hash"""

    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: UUID) -> str:
    """Create a signed JWT  identifying a user."""

    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(payload, settings.auth_secret_key, algorithm=JWT_ALGOTITHM)


def decode_access_token(token: str) -> UUID:
    """Validate an access token and return its user ID."""

    payload = jwt.decode(
        token,
        settings.auth_secret_key,
        algorithms=[JWT_ALGOTITHM],
        options={"require": ["sub", "exp"]},
    )

    subject = payload.get("sub")

    if not isinstance(subject, str):
        raise InvalidTokenError("Token subject is missing or invalid.")

    try:
        return UUID(subject)
    except ValueError as e:
        raise InvalidTokenError("Token subject is not a valid UUID.") from e
