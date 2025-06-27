from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingUpdate
from fastapi import HTTPException, status


class BookingService:
    def __init__(self, db: Session):
        self.db = db

    def create_booking(self, customer_id: int, booking_create: BookingCreate) -> Booking:
        # Check if barber exists and is active
        barber = self.db.query(User).filter(
            and_(User.id == booking_create.barber_id, User.is_active == True)
        ).first()
        
        if not barber or not barber.is_barber:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Barber not found or not active"
            )

        # Check if the requested time slot is available
        if not self._is_time_slot_available(
            booking_create.barber_id,
            booking_create.appointment_date,
            booking_create.duration_minutes
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested time slot is not available"
            )

        # Create booking
        db_booking = Booking(
            customer_id=customer_id,
            barber_id=booking_create.barber_id,
            service_name=booking_create.service_name,
            service_price=booking_create.service_price,
            appointment_date=booking_create.appointment_date,
            duration_minutes=booking_create.duration_minutes,
            notes=booking_create.notes,
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING
        )

        self.db.add(db_booking)
        self.db.commit()
        self.db.refresh(db_booking)
        return db_booking

    def get_booking_by_id(self, booking_id: int) -> Optional[Booking]:
        return self.db.query(Booking).filter(Booking.id == booking_id).first()

    def get_user_bookings(self, user_id: int, as_customer: bool = True) -> List[Booking]:
        if as_customer:
            return self.db.query(Booking).filter(Booking.customer_id == user_id).all()
        else:
            return self.db.query(Booking).filter(Booking.barber_id == user_id).all()

    def update_booking_status(self, booking_id: int, new_status: BookingStatus, user_id: int) -> Booking:
        booking = self.get_booking_by_id(booking_id)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        # Only barber can update booking status
        if booking.barber_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the barber can update booking status"
            )

        booking.status = new_status
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def cancel_booking(self, booking_id: int, user_id: int) -> Booking:
        booking = self.get_booking_by_id(booking_id)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        # Only customer or barber can cancel their own bookings
        if booking.customer_id != user_id and booking.barber_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this booking"
            )

        # Check if booking can be cancelled (not too close to appointment time)
        time_until_appointment = booking.appointment_date - datetime.utcnow()
        if time_until_appointment < timedelta(hours=2):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel booking within 2 hours of appointment"
            )

        booking.status = BookingStatus.CANCELLED
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def _is_time_slot_available(self, barber_id: int, appointment_date: datetime, duration_minutes: int) -> bool:
        # Check for overlapping bookings
        end_time = appointment_date + timedelta(minutes=duration_minutes)
        
        overlapping_bookings = self.db.query(Booking).filter(
            and_(
                Booking.barber_id == barber_id,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                or_(
                    and_(
                        Booking.appointment_date <= appointment_date,
                        Booking.appointment_date + timedelta(minutes=Booking.duration_minutes) > appointment_date
                    ),
                    and_(
                        Booking.appointment_date < end_time,
                        Booking.appointment_date + timedelta(minutes=Booking.duration_minutes) >= end_time
                    ),
                    and_(
                        Booking.appointment_date >= appointment_date,
                        Booking.appointment_date + timedelta(minutes=Booking.duration_minutes) <= end_time
                    )
                )
            )
        ).count()

        return overlapping_bookings == 0

    def get_barber_availability(self, barber_id: int, date: datetime) -> List[dict]:
        # Get all bookings for the barber on the specified date
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        bookings = self.db.query(Booking).filter(
            and_(
                Booking.barber_id == barber_id,
                Booking.appointment_date >= start_of_day,
                Booking.appointment_date < end_of_day,
                Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
            )
        ).all()

        # Generate available time slots (assuming 9 AM to 6 PM working hours)
        available_slots = []
        working_start = 9  # 9 AM
        working_end = 18   # 6 PM
        
        for hour in range(working_start, working_end):
            slot_start = start_of_day.replace(hour=hour, minute=0)
            slot_end = slot_start + timedelta(hours=1)
            
            # Check if this slot conflicts with any booking
            is_available = True
            for booking in bookings:
                booking_end = booking.appointment_date + timedelta(minutes=booking.duration_minutes)
                if (slot_start < booking_end and slot_end > booking.appointment_date):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    "start_time": slot_start,
                    "end_time": slot_end,
                    "available": True
                })

        return available_slots 