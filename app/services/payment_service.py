import stripe
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.booking import Booking, PaymentStatus
from app.core.config import settings
from fastapi import HTTPException, status

# Configure Stripe
stripe.api_key = settings.stripe_secret_key


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    def create_payment_intent(self, booking_id: int, amount: float, currency: str = "usd") -> Dict[str, Any]:
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        try:
            # Create payment intent with Stripe
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                metadata={
                    "booking_id": str(booking_id),
                    "customer_id": str(booking.customer_id),
                    "barber_id": str(booking.barber_id)
                }
            )

            # Update booking with payment intent ID
            booking.stripe_payment_intent_id = payment_intent.id
            self.db.commit()

            return {
                "client_secret": payment_intent.client_secret,
                "payment_intent_id": payment_intent.id
            }

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment intent creation failed: {str(e)}"
            )

    def confirm_payment(self, payment_intent_id: str) -> Booking:
        booking = self.db.query(Booking).filter(
            Booking.stripe_payment_intent_id == payment_intent_id
        ).first()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found for this payment"
            )

        try:
            # Retrieve payment intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent.status == "succeeded":
                booking.payment_status = PaymentStatus.PAID
                self.db.commit()
                return booking
            elif payment_intent.status == "requires_payment_method":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment requires additional authentication"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Payment failed with status: {payment_intent.status}"
                )

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment confirmation failed: {str(e)}"
            )

    def process_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )

        # Handle the event
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            return self._handle_payment_success(payment_intent)
        elif event["type"] == "payment_intent.payment_failed":
            payment_intent = event["data"]["object"]
            return self._handle_payment_failure(payment_intent)
        else:
            return {"status": "ignored", "event_type": event["type"]}

    def _handle_payment_success(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        booking = self.db.query(Booking).filter(
            Booking.stripe_payment_intent_id == payment_intent["id"]
        ).first()

        if booking:
            booking.payment_status = PaymentStatus.PAID
            self.db.commit()

        return {
            "status": "success",
            "booking_id": booking.id if booking else None,
            "payment_intent_id": payment_intent["id"]
        }

    def _handle_payment_failure(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        booking = self.db.query(Booking).filter(
            Booking.stripe_payment_intent_id == payment_intent["id"]
        ).first()

        if booking:
            booking.payment_status = PaymentStatus.FAILED
            self.db.commit()

        return {
            "status": "failed",
            "booking_id": booking.id if booking else None,
            "payment_intent_id": payment_intent["id"]
        }

    def refund_payment(self, booking_id: int) -> Dict[str, Any]:
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found"
            )

        if not booking.stripe_payment_intent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No payment found for this booking"
            )

        try:
            # Create refund
            refund = stripe.Refund.create(
                payment_intent=booking.stripe_payment_intent_id
            )

            if refund.status == "succeeded":
                booking.payment_status = PaymentStatus.REFUNDED
                self.db.commit()

            return {
                "status": "success",
                "refund_id": refund.id,
                "amount": refund.amount / 100  # Convert from cents
            }

        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Refund failed: {str(e)}"
            ) 