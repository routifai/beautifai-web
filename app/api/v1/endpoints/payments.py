from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from app.core.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.booking import PaymentIntentCreate, PaymentIntentResponse
from app.services.payment_service import PaymentService
from typing import Optional

router = APIRouter()


@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
def create_payment_intent(
    payment_data: PaymentIntentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a payment intent for a booking"""
    payment_service = PaymentService(db)
    
    # Verify that the booking belongs to the current user
    from app.models.booking import Booking
    booking = db.query(Booking).filter(
        Booking.id == payment_data.booking_id,
        Booking.customer_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    if booking.payment_status.value == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already paid"
        )
    
    result = payment_service.create_payment_intent(
        payment_data.booking_id,
        payment_data.amount,
        payment_data.currency
    )
    
    return PaymentIntentResponse(
        client_secret=result["client_secret"],
        payment_intent_id=result["payment_intent_id"]
    )


@router.post("/confirm-payment")
def confirm_payment(
    payment_intent_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Confirm a payment"""
    payment_service = PaymentService(db)
    booking = payment_service.confirm_payment(payment_intent_id)
    
    return {
        "message": "Payment confirmed successfully",
        "booking_id": booking.id,
        "payment_status": booking.payment_status.value
    }


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Handle Stripe webhooks"""
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )
    
    payload = await request.body()
    payment_service = PaymentService(db)
    
    try:
        result = payment_service.process_webhook(payload, stripe_signature)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.post("/{booking_id}/refund")
def refund_payment(
    booking_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Refund a payment (barber only)"""
    # Check if user is the barber for this booking
    from app.models.booking import Booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    if booking.barber_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the barber can refund payments"
        )
    
    payment_service = PaymentService(db)
    result = payment_service.refund_payment(booking_id)
    
    return {
        "message": "Payment refunded successfully",
        "refund_id": result["refund_id"],
        "amount": result["amount"]
    } 