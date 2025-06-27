from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.user import UserUpdate, User as UserSchema
from app.services.auth_service import AuthService

router = APIRouter()


@router.get("/me", response_model=UserSchema)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=UserSchema)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    auth_service = AuthService(db)
    updated_user = auth_service.update_user(current_user.id, user_update)
    return updated_user


@router.delete("/me")
def deactivate_current_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Deactivate current user account"""
    auth_service = AuthService(db)
    auth_service.deactivate_user(current_user.id)
    return {"message": "Account deactivated successfully"}


@router.get("/{user_id}", response_model=UserSchema)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (public profile)"""
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user 