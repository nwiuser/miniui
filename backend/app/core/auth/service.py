"""
Authentication service for handling user login, logout, and validation.
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from ...db import models
from ..security.password import verify_password, get_password_hash, ensure_valid_password
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

        # Check if account is locked. A locked account stays locked even with the
        # right password; an ADMIN unlocks it through the workspace-user update
        # endpoint, which is the only recovery path on purpose.
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

    def invalidate_user_sessions(self, user_id: int, keep_session_id: Optional[str] = None) -> int:
        """
        Deactivate all active sessions belonging to a user.

        Args:
            user_id: The workspace user ID
            keep_session_id: Optional session ID to leave active (e.g. current login)

        Returns:
            Number of sessions invalidated
        """
        query = self.db.query(models.Session).filter(
            models.Session.user_id == user_id,
            models.Session.is_active == True
        )
        if keep_session_id:
            query = query.filter(models.Session.session_id != keep_session_id)

        sessions = query.all()
        for session in sessions:
            session.is_active = False
        if sessions:
            self.db.commit()
        return len(sessions)

    def change_password(
        self,
        user: models.WorkspaceUser,
        current_password: str,
        new_password: str,
        keep_session_id: Optional[str] = None,
    ) -> bool:
        """
        Change a user's password.

        Verifies the current password, enforces the password strength policy,
        updates the stored hash, and invalidates all other active sessions for
        the user (session invalidation on password change). Resets any failed
        access attempt counters and clears the change-on-first-use flag.

        Args:
            user: The workspace user to update
            current_password: The user's current plain-text password
            new_password: The desired new plain-text password
            keep_session_id: Optional session ID to keep active

        Returns:
            True on success

        Raises:
            ValueError: Current password is wrong, or new password is too weak
        """
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        ensure_valid_password(new_password)

        user.password_hash = get_password_hash(new_password)
        user.failed_access_attempts = 0
        user.change_password_on_first_use = False
        user.account_locked = False

        self.invalidate_user_sessions(user.id, keep_session_id=keep_session_id)

        self.db.commit()
        return True

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