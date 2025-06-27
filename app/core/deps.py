from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.security import verify_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService

security = HTTPBearer()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = credentials.credentials
    username = verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = AuthService(db).get_user_by_email(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_barber(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_barber:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a barber"
        )
    return current_user


def get_current_customer(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.is_barber:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Barbers cannot access customer endpoints"
        )
    return current_user 