"""
Session State Management Service
Handles getting, setting, and managing session state values for applications.
"""
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List
import uuid
import time

from sqlalchemy.orm import Session
from ...db import models
from ...db.session import get_db


class SessionService:
    """Service for managing application session state."""

    def __init__(self, db: Session):
        self.db = db
        self.last_cleanup = None

    def _periodic_cleanup(self):
        """
        Periodically clean up expired sessions (at most once per hour).
        """
        # Initialize last_cleanup if it's None
        if self.last_cleanup is None:
            self.last_cleanup = datetime.utcnow()
            return

        # Check if it's been more than 1 hour since last cleanup
        if datetime.utcnow() - self.last_cleanup > timedelta(hours=1):
            # Run cleanup
            self.cleanup_expired_sessions()
            # Update last cleanup time
            self.last_cleanup = datetime.utcnow() iaitu

    def create_session(self, application_id: int, user_id: Optional[int] = None) -> str:
        """
        Create a new session for an application.

        Args:
            application_id: The ID of the application
            user_id: Optional user ID if authenticated

        Returns:
            Session ID string
        """
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hour session

        db_session = models.Session(
            session_id=session_id,
            application_id=application_id,
            user_id=user_id,
            expires_at=expires_at
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)

        return session_id

    def get_session(self, session_id: str) -> Optional[models.Session]:
        """
        Get a session by its session ID.

        Args:
            session_id: The session ID string

        Returns:
            Session object if found and not expired, None otherwise
        """
        # Periodically clean up expired sessions (at most once per hour)
        self._periodic_cleanup()

        session = self.db.query(models.Session).filter(
            models.Session.session_id == session_id,
            models.Session.is_active == True,
            models.Session.expires_at > datetime.utcnow()
        ).first()

        return session

    def validate_session(self, session_id: str) -> bool:
        """
        Check if a session is valid (exists, active, not expired).

        Args:
            session_id: The session ID string

        Returns:
            True if session is valid, False otherwise
        """
        return self.get_session(session_id) is not None

    def set_item(self, session_id: str, page_id: int, item_name: str, value: Any) -> bool:
        """
        Set a session state item value.

        Args:
            session_id: The session ID string
            page_id: The page ID this item belongs to
            item_name: The name of the item (e.g., 'P1_FIELD_NAME')
            value: The value to store (will be converted to string)

        Returns:
            True if successful, False if session is invalid
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # Convert value to string for storage
        str_value = str(value) if value is not None else ""

        # Check if item already exists
        item = self.db.query(models.SessionStateItem).filter(
            models.SessionStateItem.session_id == session.id,
            models.SessionStateItem.page_id == page_id,
            models.SessionStateItem.item_name == item_name
        ).first()

        if item:
            # Update existing item
            item.item_value = str_value
            item.updated_at = datetime.utcnow()
        else:
            # Create new item
            item = models.SessionStateItem(
                session_id=session.id,
                page_id=page_id,
                item_name=item_name,
                item_value=str_value
            )
            self.db.add(item)

        self.db.commit()
        return True

    def get_item(self, session_id: str, page_id: int, item_name: str) -> Optional[str]:
        """
        Get a session state item value.

        Args:
            session_id: The session ID string
            page_id: The page ID this item belongs to
            item_name: The name of the item (e.g., 'P1_FIELD_NAME')

        Returns:
            The item value as string, or None if not found or session invalid
        """
        session = self.get_session(session_id)
        if not session:
            return None

        item = self.db.query(models.SessionStateItem).filter(
            models.SessionStateItem.session_id == session.id,
            models.SessionStateItem.page_id == page_id,
            models.SessionStateItem.item_name == item_name
        ).first()

        return item.item_value if item else None

    def get_items_for_page(self, session_id: str, page_id: int) -> dict:
        """
        Get all session state items for a specific page.

        Args:
            session_id: The session ID string
            page_id: The page ID

        Returns:
            Dictionary of item names to values
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        items = self.db.query(models.SessionStateItem).filter(
            models.SessionStateItem.session_id == session.id,
            models.SessionStateItem.page_id == page_id
        ).all()

        return {item.item_name: item.item_value for item in items}

    def clear_session(self, session_id: str) -> bool:
        """
        Clear/invalidate a session.

        Args:
            session_id: The session ID string

        Returns:
            True if successful, False if session not found
        """
        session = self.db.query(models.Session).filter(
            models.Session.session_id == session_id
        ).first()

        if session:
            session.is_active = False
            self.db.commit()
            return True
        return False

    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from the database.

        Returns:
            Number of sessions removed
        """
        expired_sessions = self.db.query(models.Session).filter(
            models.Session.expires_at <= datetime.utcnow()
        ).all()

        count = len(expired_sessions)
        for session in expired_sessions:
            self.db.delete(session)

        self.db.commit()
        return count