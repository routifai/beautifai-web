from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.deps import get_current_active_user, get_current_barber, get_db
from app.models.user import User
from app.models.booking import Booking, BookingStatus
from app.schemas.booking import BookingCreate, BookingUpdate, Booking as BookingSchema, BookingStatusUpdate
from app.services.booking_service import BookingService

router = APIRouter()


@router.post("/", response_model=BookingSchema)
def create_booking(
    booking_create: BookingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new booking"""
    booking_service = BookingService(db)
    booking = booking_service.create_booking(current_user.id, booking_create)
    return booking


@router.get("/", response_model=List[BookingSchema])
def get_my_bookings(
    as_customer: bool = Query(True, description="Get bookings as customer or barber"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's bookings (as customer or barber)"""
    booking_service = BookingService(db)
    bookings = booking_service.get_user_bookings(current_user.id, as_customer=as_customer)
    return bookings


@router.get("/{booking_id}", response_model=BookingSchema)
def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get booking by ID"""
    booking_service = BookingService(db)
    booking = booking_service.get_booking_by_id(booking_id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    # Check if user has access to this booking
    if booking.customer_id != current_user.id and booking.barber_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this booking"
        )
    
    return booking


@router.put("/{booking_id}/status", response_model=BookingSchema)
def update_booking_status(
    booking_id: int,
    status_update: BookingStatusUpdate,
    current_user: User = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Update booking status (barber only)"""
    booking_service = BookingService(db)
    booking = booking_service.update_booking_status(
        booking_id, status_update.status, current_user.id
    )
    return booking


@router.delete("/{booking_id}")
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel a booking"""
    booking_service = BookingService(db)
    booking = booking_service.cancel_booking(booking_id, current_user.id)
    return {"message": "Booking cancelled successfully"}


@router.get("/barber/{barber_id}/availability")
def get_barber_availability(
    barber_id: int,
    date: datetime = Query(..., description="Date to check availability"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get barber availability for a specific date"""
    booking_service = BookingService(db)
    availability = booking_service.get_barber_availability(barber_id, date)
    return {"barber_id": barber_id, "date": date, "availability": availability}


@router.get("/barber/{barber_id}/bookings", response_model=List[BookingSchema])
def get_barber_bookings(
    barber_id: int,
    current_user: User = Depends(get_current_barber),
    db: Session = Depends(get_db)
):
    """Get all bookings for a barber (barber only)"""
    if current_user.id != barber_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only access own bookings"
        )
    
    booking_service = BookingService(db)
    bookings = booking_service.get_user_bookings(barber_id, as_customer=False)
    return bookings 