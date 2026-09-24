"""
Password security utilities.

Uses the ``bcrypt`` library directly. The previous ``passlib``-based
implementation is incompatible with bcrypt >= 4 on Python 3.12 (passlib reads
``bcrypt.__about__``, which was removed), and passlib is unmaintained.
"""
import bcrypt

# bcrypt silently truncates input at 72 bytes; surface the limit explicitly.
MAX_PASSWORD_LEN = 72


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        # Malformed hash or otherwise unverifiable -> treat as no match.
        return False


def get_password_hash(password: str) -> str:
    """Generate a bcrypt password hash."""
    if len(password.encode("utf-8")) > MAX_PASSWORD_LEN:
        raise ValueError(f"password cannot be longer than {MAX_PASSWORD_LEN} bytes")
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
