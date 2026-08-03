"""
Authentication service for handling user login, logout, and validation.
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from ..db import models
from ..core.security.password_utils import verify_password
from ..session.service import SessionService


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, db: Session):
        self.db = db
        self.session_service = SessionService(db)
        # Configuration for account lockout
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30  # Optional: could implement timed lockout

    def authenticate_user(self, username: str, password: str) -> Optional[models.WorkspaceUser]:
        """
        Authenticate a user with username and password.

        Args:
            username: User's username
            password: User's plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        # Get user by username
        user = self.db.query(models.WorkspaceUser).filter(
            models.WorkspaceUser.username == username
        ).first()

        if not user:
            # User not found - treat as failed attempt to avoid user enumeration
            # (but we don't have a user record to update)
            return None

        # Check if account is locked
        if user.account_locked:
            return None

        # Verify password
        if not verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_access_attempts += 1
            if user.failed_access_attempts >= self.max_failed_attempts:
                user.account_locked = True
                # Optionally set lockout timestamp if column existed
            self.db.commit()
            return None

        # Password correct - reset failed attempts and return user
        user.failed_access_attempts = 0
        # Ensure account is unlocked (in case it was locked previously)
        if user.account_locked:
            user.account_locked = False
        self.db.commit()

        # Check if password needs to be changed on first use
        # TODO: Implement password change requirement logic

        return user

    def login(self, username: str, password: str, application_id: int) -> tuple[str, dict]:
        """
        Authenticate user and create a session.

        Args:
            username: User's username
            password: User's plain text password
            application_id: ID of the application to create session for

        Returns:
            Tuple of (session_id, user_info_dict)

        Raises:
            ValueError: If authentication fails
        """
        # Authenticate user
        user = self.authenticate_user(username, password)
        if not user:
            raise ValueError("Invalid username or password")

        # Create session
        session_id = self.session_service.create_session(
            application_id=application_id,
            user_id=user.id
        )

        # Reset failed login attempts on successful login
        user.failed_access_attempts = 0
        self.db.commit()

        # Return session info and user data (excluding sensitive info)
        user_info = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "administrator_role": user.administrator_role,
            "password_change_required": user.change_password_on_first_use
        }

        return session_id, user_info

    def logout(self, session_id: str) -> bool:
        """
        Log out a user by invalidating their session.

        Args:
            session_id: Session ID to invalidate

        Returns:
            True if successful, False if session not found
        """
        return self.session_service.clear_session(session_id)

    def get_current_user(self, session_id: str) -> Optional[models.WorkspaceUser]:
        """
        Get the current user from a session ID.

        Args:
            session_id: Session ID

        Returns:
            User object if valid session, None otherwise
        """
        session = self.session_service.get_session(session_id)
        if not session:
            return None

        return session.user