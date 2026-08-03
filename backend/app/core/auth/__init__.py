"""
Authentication package containing authentication service and related utilities.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..db.session import get_db
from .. import models
from .service import AuthService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(session_id: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency to get the current authenticated user from the session ID.
    """
    auth_service = AuthService(db)
    user = auth_service.get_current_user(session_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_session(session_id: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency to get the current session from the session ID.
    """
    auth_service = AuthService(db)
    session = auth_service.session_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return session


def get_current_application(current_session = Depends(get_current_session), db: Session = Depends(get_db)):
    """
    Dependency to get the current application from the session.
    """
    application = db.query(models.Application).filter(
        models.Application.id == current_session.application_id
    ).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    return application


def get_current_user_optional(session_id: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependency to get the current authenticated user from the session ID.
    Returns None if not authenticated instead of raising an exception.
    """
    auth_service = AuthService(db)
    return auth_service.get_current_user(session_id)


def require_role(*allowed_roles: str):
    """
    Dependency to check if the current user has one of the allowed roles.
    Usage: dependencies = [Depends(require_role("ADMIN", "DEVELOPER"))]
    """
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.administrator_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return Depends(role_checker)


def application_access_required(application_id: int):
    """
    Dependency to check if the current user has access to the specified application.
    - ADMIN and DEVELOPER roles have access to all applications
    - END_USER role only has access to the application in their current session
    """
    def _application_access_checker(
        current_user = Depends(get_current_user),
        current_session = Depends(get_current_session),
        db: Session = Depends(get_db)
    ):
        # ADMIN and DEVELOPER can access any application
        if current_user.administrator_role in ["ADMIN", "DEVELOPER"]:
            # Still verify the application exists
            application = db.query(models.Application).filter(
                models.Application.id == application_id
            ).first()
            if not application:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Application not found"
                )
            return current_user

        # END_USER can only access the application in their current session
        if current_session.application_id != application_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this application"
            )

        # Verify the application exists
        application = db.query(models.Application).filter(
            models.Application.id == application_id
        ).first()
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )

        return current_user
    return Depends(_application_access_checker)