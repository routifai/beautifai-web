from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class BarberBase(BaseModel):
    shop_name: Optional[str] = None
    specialties: Optional[List[str]] = None
    services: Optional[Dict[str, Any]] = None
    working_hours: Optional[Dict[str, Any]] = None
    is_available: bool = True


class BarberCreate(BarberBase):
    pass


class BarberUpdate(BarberBase):
    pass


class BarberInDB(BarberBase):
    id: int
    user_id: int
    rating: float
    total_reviews: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Barber(BarberInDB):
    pass


class BarberWithUser(Barber):
    user: "User"  # Forward reference to avoid circular import


class ReviewBase(BaseModel):
    rating: int
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    barber_id: int


class ReviewInDB(ReviewBase):
    id: int
    barber_id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Review(ReviewInDB):
    pass


class BarberSearchParams(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = 10.0
    service: Optional[str] = None
    min_rating: Optional[float] = None
    max_price: Optional[float] = None
    available_date: Optional[datetime] = None 