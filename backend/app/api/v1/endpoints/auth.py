from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..core.auth.service import AuthService
from ..db.session import get_db

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/login", response_model=schemas.Token)
def login(
    username: str = Form(...),
    password: str = Form(...),
    application_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Login to get a session token (acting as access token in this MVP).
    """
    # Authenticate user
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create session
    session_id, user_info = auth_service.login(
        username=username,
        password=password,
        application_id=application_id
    )

    # Build token response with user info
    token_data = {
        "access_token": session_id,
        "token_type": "bearer",
        "user_id": user_info.get("id"),
        "username": user_info.get("username"),
        "email": user_info.get("email"),
        "first_name": user_info.get("first_name"),
        "last_name": user_info.get("last_name"),
        "administrator_role": user_info.get("administrator_role"),
    }
    return token_data

@router.post("/logout")
def logout(
    session_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Log out user by invalidating the session.
    """
    auth_service = AuthService(db)
    success = auth_service.logout(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session"
        )
    return {"msg": "Successfully logged out"}