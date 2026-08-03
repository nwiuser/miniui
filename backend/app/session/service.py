"""
Session service for managing user sessions.
"""
from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import Session
from .. import models

class SessionService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, user_id: int, application_id: int) -> str:
        """Create a new session for the user."""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hour session

        db_session = models.Session(
            session_id=session_id,
            user_id=user_id,
            application_id=application_id,
            expires_at=expires_at,
            is_active=True
        )
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return session_id

    def get_session(self, session_id: str):
        """Get a session by session ID."""
        return self.db.query(models.Session).filter(
            models.Session.session_id == session_id,
            models.Session.is_active == True,
            models.Session.expires_at > datetime.utcnow()
        ).first()

    def clear_session(self, session_id: str) -> bool:
        """Invalidate a session."""
        session = self.db.query(models.Session).filter(
            models.Session.session_id == session_id
        ).first()
        if session:
            session.is_active = False
            self.db.commit()
            return True
        return False

    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired_sessions = self.db.query(models.Session).filter(
            models.Session.expires_at <= now
        ).all()
        for session in expired_sessions:
            self.db.delete(session)
        self.db.commit()