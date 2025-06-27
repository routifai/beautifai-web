from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.booking import BookingStatus, PaymentStatus


class BookingBase(BaseModel):
    service_name: str
    service_price: float
    appointment_date: datetime
    duration_minutes: int = 60
    notes: Optional[str] = None


class BookingCreate(BookingBase):
    barber_id: int


class BookingUpdate(BaseModel):
    appointment_date: Optional[datetime] = None
    status: Optional[BookingStatus] = None
    notes: Optional[str] = None


class BookingInDB(BookingBase):
    id: int
    customer_id: int
    barber_id: int
    status: BookingStatus
    payment_status: PaymentStatus
    stripe_payment_intent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Booking(BookingInDB):
    pass


class BookingWithRelations(Booking):
    customer: "User"  # Forward reference
    barber: "User"    # Forward reference


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


class PaymentIntentCreate(BaseModel):
    booking_id: int
    amount: float
    currency: str = "usd"


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str 