from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class Booking(BaseModel):
    customer_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    barber_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    service_name = Column(String(200), nullable=False)
    service_price = Column(Float, nullable=False)
    appointment_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    notes = Column(Text, nullable=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    
    # Relationships
    customer = relationship("User", back_populates="bookings_as_customer", foreign_keys=[customer_id])
    barber = relationship("User", back_populates="bookings_as_barber", foreign_keys=[barber_id])
    
    def __repr__(self):
        return f"<Booking(id={self.id}, customer_id={self.customer_id}, barber_id={self.barber_id}, status='{self.status}')>" 