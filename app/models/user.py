from sqlalchemy import Column, String, Boolean, Text, Float, Integer
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class User(BaseModel):
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_barber = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Barber-specific fields
    bio = Column(Text, nullable=True)
    experience_years = Column(Integer, nullable=True)
    hourly_rate = Column(Float, nullable=True)
    address = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Relationships
    barber_profile = relationship("Barber", back_populates="user", uselist=False)
    bookings_as_customer = relationship("Booking", back_populates="customer", foreign_keys="Booking.customer_id")
    bookings_as_barber = relationship("Booking", back_populates="barber", foreign_keys="Booking.barber_id")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', is_barber={self.is_barber})>" 