from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.deps import get_current_active_user, get_current_barber, get_db
from app.models.user import User
from app.models.barber import Barber, Review
from app.schemas.barber import BarberCreate, BarberUpdate, Barber as BarberSchema, ReviewCreate, Review as ReviewSchema, BarberSearchParams
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/profile", response_model=BarberSchema)
def create_barber_profile(
    barber_create: BarberCreate,
    current_user: User = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Create barber profile"""
    # Check if barber profile already exists
    existing_profile = db.query(Barber).filter(Barber.user_id == current_user.id).first()
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Barber profile already exists"
        )
    
    # Create barber profile
    db_barber = Barber(
        user_id=current_user.id,
        shop_name=barber_create.shop_name,
        specialties=barber_create.specialties,
        services=barber_create.services,
        working_hours=barber_create.working_hours,
        is_available=barber_create.is_available
    )
    
    db.add(db_barber)
    db.commit()
    db.refresh(db_barber)
    return db_barber


@router.get("/profile", response_model=BarberSchema)
def get_barber_profile(
    current_user: User = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Get current barber profile"""
    barber = db.query(Barber).filter(Barber.user_id == current_user.id).first()
    if not barber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barber profile not found"
        )
    return barber


@router.put("/profile", response_model=BarberSchema)
def update_barber_profile(
    barber_update: BarberUpdate,
    current_user: User = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Update barber profile"""
    barber = db.query(Barber).filter(Barber.user_id == current_user.id).first()
    if not barber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barber profile not found"
        )
    
    update_data = barber_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(barber, field, value)
    
    db.commit()
    db.refresh(barber)
    return barber


@router.get("/search", response_model=List[BarberSchema])
def search_barbers(
    latitude: Optional[float] = Query(None, description="Latitude for location-based search"),
    longitude: Optional[float] = Query(None, description="Longitude for location-based search"),
    radius_km: float = Query(10.0, description="Search radius in kilometers"),
    service: Optional[str] = Query(None, description="Service to search for"),
    min_rating: Optional[float] = Query(None, description="Minimum rating"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    db: Session = Depends(get_db)
):
    """Search for barbers with filters"""
    query = db.query(Barber).join(User).filter(User.is_active == True, Barber.is_available == True)
    
    # Filter by service if provided
    if service:
        query = query.filter(Barber.services.contains([service]))
    
    # Filter by minimum rating
    if min_rating:
        query = query.filter(Barber.rating >= min_rating)
    
    # Filter by maximum price (assuming hourly_rate is stored)
    if max_price:
        query = query.join(User).filter(User.hourly_rate <= max_price)
    
    # Location-based filtering (simplified - in production, use proper geospatial queries)
    if latitude and longitude:
        # This is a simplified distance calculation
        # In production, use PostGIS or similar for proper geospatial queries
        pass
    
    barbers = query.all()
    return barbers


@router.get("/{barber_id}", response_model=BarberSchema)
def get_barber_by_id(
    barber_id: int,
    db: Session = Depends(get_db)
):
    """Get barber by ID"""
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barber not found"
        )
    return barber


@router.post("/{barber_id}/reviews", response_model=ReviewSchema)
def create_review(
    barber_id: int,
    review_create: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a review for a barber"""
    # Check if barber exists
    barber = db.query(Barber).filter(Barber.id == barber_id).first()
    if not barber:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Barber not found"
        )
    
    # Check if user has already reviewed this barber
    existing_review = db.query(Review).filter(
        Review.barber_id == barber_id,
        Review.customer_id == current_user.id
    ).first()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this barber"
        )
    
    # Create review
    db_review = Review(
        barber_id=barber_id,
        customer_id=current_user.id,
        rating=review_create.rating,
        comment=review_create.comment
    )
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Update barber rating
    reviews = db.query(Review).filter(Review.barber_id == barber_id).all()
    total_rating = sum(review.rating for review in reviews)
    barber.rating = total_rating / len(reviews)
    barber.total_reviews = len(reviews)
    db.commit()
    
    return db_review


@router.get("/{barber_id}/reviews", response_model=List[ReviewSchema])
def get_barber_reviews(
    barber_id: int,
    db: Session = Depends(get_db)
):
    """Get all reviews for a barber"""
    reviews = db.query(Review).filter(Review.barber_id == barber_id).all()
    return reviews 