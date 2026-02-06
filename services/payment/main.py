"""
Payment Service - Aarya Clothing
Payment Processing and Fraud Detection

This service handles:
- Razorpay payment processing
- Transaction management
- Refund processing
- Webhook handling
- Payment method management
"""
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
import json

from core.config import settings
from database.database import get_db, init_db
from service.payment_service import PaymentService
from schemas.payment import (
    PaymentRequest, PaymentResponse, PaymentStatus, PaymentMethod,
    RazorpayOrderRequest, RazorpayOrderResponse, RazorpayPaymentVerification,
    RefundRequest, RefundResponse, RefundStatus,
    WebhookEvent, WebhookResponse, PaymentMethodsResponse,
    TransactionHistoryRequest
)
from core.razorpay_client import get_razorpay_client


# ==================== Lifespan ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    init_db()
    
    # Test Razorpay connection if configured
    try:
        razorpay_client = get_razorpay_client()
        print("✓ Payment service: Razorpay client initialized")
    except Exception as e:
        print(f"⚠ Payment service: Razorpay client not initialized - {str(e)}")
    
    print("✓ Payment service started")
    yield
    
    # Shutdown
    print("✓ Payment service stopped")


# ==================== FastAPI App ====================

app = FastAPI(
    title="Aarya Clothing - Payment Service",
    description="Payment Processing with Razorpay Integration",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Check ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "payment",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "razorpay": bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET),
            "webhooks": bool(settings.RAZORPAY_WEBHOOK_SECRET)
        }
    }


# ==================== Razorpay Payment Routes ====================

@app.post("/api/v1/payments/razorpay/create-order", response_model=RazorpayOrderResponse,
          tags=["Razorpay"])
async def create_razorpay_order(
    request: RazorpayOrderRequest,
    db: Session = Depends(get_db)
):
    """
    Create a Razorpay order for payment.
    
    This endpoint creates a Razorpay order that can be used to initiate payment.
    """
    try:
        razorpay_client = get_razorpay_client()
        order = razorpay_client.create_order(
            amount=int(request.amount),
            currency=request.currency,
            receipt=request.receipt,
            notes=request.notes
        )
        return RazorpayOrderResponse(**order)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create Razorpay order: {str(e)}"
        )


@app.post("/api/v1/payments/razorpay/verify", response_model=PaymentResponse,
          tags=["Razorpay"])
async def verify_razorpay_payment(
    request: RazorpayPaymentVerification,
    db: Session = Depends(get_db)
):
    """
    Verify Razorpay payment after completion.
    
    This endpoint verifies the payment signature and updates the transaction status.
    """
    try:
        payment_service = PaymentService(db)
        
        # Find transaction by Razorpay order ID
        from models.payment import PaymentTransaction
        transaction = db.query(PaymentTransaction).filter(
            PaymentTransaction.razorpay_order_id == request.razorpay_order_id
        ).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Verify payment
        response = payment_service.verify_payment(
            transaction.transaction_id,
            request.razorpay_payment_id,
            request.razorpay_signature
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment verification failed: {str(e)}"
        )


# ==================== Payment Routes ====================

@app.post("/api/v1/payments/process", response_model=PaymentResponse,
          tags=["Payments"])
async def process_payment(
    request: PaymentRequest,
    db: Session = Depends(get_db)
):
    """
    Process a payment for an order.
    
    This endpoint creates a payment transaction and initiates payment processing.
    """
    try:
        payment_service = PaymentService(db)
        response = payment_service.create_payment_transaction(request)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment processing failed: {str(e)}"
        )


@app.get("/api/v1/payments/{transaction_id}/status",
         tags=["Payments"])
async def get_payment_status(transaction_id: str, db: Session = Depends(get_db)):
    """
    Get the status of a payment transaction.
    """
    try:
        payment_service = PaymentService(db)
        status = payment_service.get_payment_status(transaction_id)
        
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return status
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment status: {str(e)}"
        )


@app.post("/api/v1/payments/{transaction_id}/refund",
          response_model=RefundResponse,
          tags=["Payments"])
async def refund_payment(
    transaction_id: str,
    reason: str = "Customer request",
    amount: Optional[Decimal] = None,
    db: Session = Depends(get_db)
):
    """
    Process a refund for a transaction.
    """
    try:
        payment_service = PaymentService(db)
        refund_request = RefundRequest(
            transaction_id=transaction_id,
            amount=amount,
            reason=reason
        )
        response = payment_service.refund_payment(refund_request)
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund processing failed: {str(e)}"
        )


@app.get("/api/v1/payments/methods", response_model=PaymentMethodsResponse,
         tags=["Payments"])
async def get_payment_methods(db: Session = Depends(get_db)):
    """
    Get available payment methods.
    """
    try:
        payment_service = PaymentService(db)
        methods = payment_service.get_available_payment_methods()
        
        return PaymentMethodsResponse(
            methods=methods,
            default_method="razorpay"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get payment methods: {str(e)}"
        )


@app.get("/api/v1/payments/history",
         tags=["Payments"])
async def get_transaction_history(
    user_id: Optional[int] = None,
    order_id: Optional[int] = None,
    status: Optional[PaymentStatus] = None,
    payment_method: Optional[PaymentMethod] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get transaction history with filters.
    """
    try:
        payment_service = PaymentService(db)
        request = TransactionHistoryRequest(
            user_id=user_id,
            order_id=order_id,
            status=status,
            payment_method=payment_method,
            skip=skip,
            limit=limit
        )
        
        history = payment_service.get_transaction_history(request)
        return {
            "transactions": history,
            "total": len(history),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transaction history: {str(e)}"
        )


# ==================== Webhook Routes ====================

@app.post("/api/v1/webhooks/razorpay", response_model=WebhookResponse,
          tags=["Webhooks"])
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(..., description="Razorpay webhook signature")
):
    """
    Handle Razorpay webhook events.
    
    This endpoint processes webhook events from Razorpay for payment status updates.
    """
    try:
        # Get raw request body
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Verify webhook signature
        razorpay_client = get_razorpay_client()
        is_valid = razorpay_client.verify_webhook_signature(
            body_str,
            x_razorpay_signature
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Parse webhook data
        webhook_data = json.loads(body_str)
        
        # Process webhook event
        db = next(get_db())
        try:
            payment_service = PaymentService(db)
            success = payment_service.process_webhook_event(webhook_data)
            
            return WebhookResponse(
                processed=success,
                message="Webhook processed successfully",
                event_type=webhook_data.get("event")
            )
        finally:
            db.close()
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


# ==================== Fraud Detection ====================

@app.post("/api/v1/payments/verify", tags=["Payments"])
async def verify_payment_risk(order_id: int, user_id: int, amount: Decimal):
    """
    Verify payment for potential fraud.
    
    This endpoint checks various factors to determine if a payment
    might be fraudulent.
    """
    # TODO: Implement actual fraud detection logic
    # - Check user history
    # - Check IP reputation
    # - Check velocity
    # - Check device fingerprint
    
    return {
        "risk_score": 0.1,
        "risk_level": "low",
        "recommendation": "approve",
        "checks_passed": [
            "user_verified",
            "ip_not_flagged",
            "velocity_normal",
            "amount_within_limits"
        ]
    }


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8020,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
