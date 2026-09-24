"""
Password security utilities.

Uses the ``bcrypt`` library directly. The previous ``passlib``-based
implementation is incompatible with bcrypt >= 4 on Python 3.12 (passlib reads
``bcrypt.__about__``, which was removed), and passlib is unmaintained.
"""
import bcrypt
import re

# bcrypt silently truncates input at 72 bytes; surface the limit explicitly.
MAX_PASSWORD_LEN = 72

# Minimum password strength policy (Phase 5).
MIN_PASSWORD_LEN = 10

PASSWORD_POLICY = {
    "min_length": MIN_PASSWORD_LEN,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
}


def validate_password_strength(password: str) -> list[str]:
    """
    Validate a password against the minimum strength policy.

    Returns a list of human-readable policy violations. An empty list means
    the password satisfies the policy.
    """
    errors: list[str] = []

    if not password:
        errors.append("Password cannot be empty.")
        return errors

    if len(password) < MIN_PASSWORD_LEN:
        errors.append(f"Password must be at least {MIN_PASSWORD_LEN} characters long.")

    if len(password.encode("utf-8")) > MAX_PASSWORD_LEN:
        errors.append(f"Password cannot be longer than {MAX_PASSWORD_LEN} bytes.")

    if PASSWORD_POLICY["require_uppercase"] and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")

    if PASSWORD_POLICY["require_lowercase"] and not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")

    if PASSWORD_POLICY["require_digit"] and not re.search(r"\d", password):
        errors.append("Password must contain at least one digit.")

    if PASSWORD_POLICY["require_special"] and not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Password must contain at least one special character.")

    return errors


def ensure_valid_password(password: str) -> None:
    """
    Raise ValueError with a joined policy message if password is too weak.
    """
    errors = validate_password_strength(password)
    if errors:
        raise ValueError(" ".join(errors))


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
