from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Barber(BaseModel):
    user_id = Column(Integer, ForeignKey("user.id"), unique=True, nullable=False)
    shop_name = Column(String(200), nullable=True)
    specialties = Column(JSON, nullable=True)  # List of specialties
    services = Column(JSON, nullable=True)  # List of services with prices
    working_hours = Column(JSON, nullable=True)  # Working hours for each day
    rating = Column(Float, default=0.0, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="barber_profile")
    reviews = relationship("Review", back_populates="barber")
    
    def __repr__(self):
        return f"<Barber(id={self.id}, user_id={self.user_id}, shop_name='{self.shop_name}')>"


class Review(BaseModel):
    barber_id = Column(Integer, ForeignKey("barber.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)
    
    # Relationships
    barber = relationship("Barber", back_populates="reviews")
    customer = relationship("User")
    
    def __repr__(self):
        return f"<Review(id={self.id}, barber_id={self.barber_id}, rating={self.rating})>" 