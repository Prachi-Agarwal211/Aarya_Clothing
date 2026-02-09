"""Payment service for handling payment transactions."""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid

from core.config import settings
from core.razorpay_client import get_razorpay_client
from models.payment import PaymentTransaction, WebhookEvent
from schemas.payment import (
    PaymentRequest, PaymentResponse, PaymentStatus, PaymentMethod,
    RefundRequest, RefundResponse, RefundStatus, TransactionHistoryRequest
)


class PaymentService:
    """Service for handling payment operations."""
    
    def __init__(self, db: Session):
        """Initialize payment service."""
        self.db = db
    
    def create_payment_transaction(self, request: PaymentRequest) -> PaymentResponse:
        """
        Create a new payment transaction.
        
        Args:
            request: Payment request data
            
        Returns:
            Payment response with transaction details
        """
        try:
            # Generate unique transaction ID
            transaction_id = f"txn_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # Create transaction record
            transaction = PaymentTransaction(
                order_id=request.order_id,
                user_id=request.user_id,
                amount=request.amount,
                currency=request.currency,
                payment_method=request.payment_method.value,
                transaction_id=transaction_id,
                status="pending",
                customer_email=request.customer_email,
                customer_phone=request.customer_phone,
                description=request.description
            )
            
            self.db.add(transaction)
            self.db.flush()
            
            # Process based on payment method
            if request.payment_method == PaymentMethod.RAZORPAY:
                return self._process_razorpay_payment(transaction, request)
            else:
                raise ValueError(f"Payment method {request.payment_method} not supported")
                
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create payment transaction: {str(e)}")
    
    def _process_razorpay_payment(self, transaction: PaymentTransaction, 
                                 request: PaymentRequest) -> PaymentResponse:
        """Process Razorpay payment."""
        try:
            # Convert amount to paise (Razorpay uses smallest currency unit)
            amount_paise = int(request.amount * 100)
            
            # Create Razorpay order
            razorpay_client = get_razorpay_client()
            razorpay_order = razorpay_client.create_order(
                amount=amount_paise,
                currency=request.currency,
                receipt=transaction.transaction_id,
                notes={
                    "order_id": str(request.order_id),
                    "user_id": str(request.user_id),
                    "transaction_id": transaction.transaction_id
                }
            )
            
            # Update transaction with Razorpay order ID
            transaction.razorpay_order_id = razorpay_order["id"]
            transaction.gateway_response = razorpay_order
            self.db.commit()
            
            return PaymentResponse(
                success=True,
                transaction_id=transaction.transaction_id,
                status=PaymentStatus.PENDING,
                message="Payment order created successfully",
                amount=request.amount,
                currency=request.currency,
                payment_method=request.payment_method,
                razorpay_order_id=razorpay_order["id"],
                gateway_response=razorpay_order
            )
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to process Razorpay payment: {str(e)}")
    
    def verify_payment(self, transaction_id: str, 
                     razorpay_payment_id: str,
                     razorpay_signature: str) -> PaymentResponse:
        """
        Verify and complete a payment transaction.
        
        Args:
            transaction_id: Transaction ID
            razorpay_payment_id: Razorpay payment ID
            razorpay_signature: Razorpay signature
            
        Returns:
            Payment verification response
        """
        try:
            # Get transaction
            transaction = self.db.query(PaymentTransaction).filter(
                PaymentTransaction.transaction_id == transaction_id
            ).first()
            
            if not transaction:
                raise ValueError("Transaction not found")
            
            if transaction.status != "pending":
                raise ValueError(f"Transaction already {transaction.status}")
            
            # Verify payment signature
            razorpay_client = get_razorpay_client()
            is_valid = razorpay_client.verify_payment(
                transaction.razorpay_order_id,
                razorpay_payment_id,
                razorpay_signature
            )
            
            if not is_valid:
                transaction.status = "failed"
                self.db.commit()
                raise ValueError("Invalid payment signature")
            
            # Fetch payment details from Razorpay
            payment_details = razorpay_client.fetch_payment(razorpay_payment_id)
            
            # Update transaction
            transaction.razorpay_payment_id = razorpay_payment_id
            transaction.razorpay_signature = razorpay_signature
            transaction.status = "completed" if payment_details.get("status") == "captured" else "failed"
            transaction.gateway_response = payment_details
            transaction.completed_at = datetime.utcnow()
            
            self.db.commit()
            
            return PaymentResponse(
                success=transaction.status == "completed",
                transaction_id=transaction.transaction_id,
                status=PaymentStatus.COMPLETED if transaction.status == "completed" else PaymentStatus.FAILED,
                message="Payment verified successfully" if transaction.status == "completed" else "Payment verification failed",
                amount=transaction.amount,
                currency=transaction.currency,
                payment_method=PaymentMethod(transaction.payment_method),
                razorpay_payment_id=razorpay_payment_id,
                gateway_response=payment_details
            )
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Payment verification failed: {str(e)}")
    
    def get_payment_status(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Get payment transaction status.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction status details
        """
        try:
            transaction = self.db.query(PaymentTransaction).filter(
                PaymentTransaction.transaction_id == transaction_id
            ).first()
            
            if not transaction:
                return None
            
            return {
                "transaction_id": transaction.transaction_id,
                "order_id": transaction.order_id,
                "user_id": transaction.user_id,
                "amount": float(transaction.amount),
                "currency": transaction.currency,
                "status": transaction.status,
                "payment_method": transaction.payment_method,
                "created_at": transaction.created_at,
                "updated_at": transaction.updated_at,
                "completed_at": transaction.completed_at,
                "razorpay_order_id": transaction.razorpay_order_id,
                "razorpay_payment_id": transaction.razorpay_payment_id,
                "refund_amount": float(transaction.refund_amount) if transaction.refund_amount else None,
                "refund_id": transaction.refund_id,
                "refund_status": transaction.refund_status,
                "refund_reason": transaction.refund_reason
            }
            
        except Exception as e:
            raise Exception(f"Failed to get payment status: {str(e)}")
    
    def refund_payment(self, request: RefundRequest) -> RefundResponse:
        """
        Process a refund for a transaction.
        
        Args:
            request: Refund request
            
        Returns:
            Refund response
        """
        try:
            # Get transaction
            transaction = self.db.query(PaymentTransaction).filter(
                PaymentTransaction.transaction_id == request.transaction_id
            ).first()
            
            if not transaction:
                raise ValueError("Transaction not found")
            
            if transaction.status != "completed":
                raise ValueError("Cannot refund incomplete transaction")
            
            if transaction.refund_status == "completed":
                raise ValueError("Transaction already refunded")
            
            # Determine refund amount
            refund_amount = request.amount if request.amount else transaction.amount
            
            # Process refund with Razorpay
            razorpay_client = get_razorpay_client()
            refund_paise = int(refund_amount * 100)
            refund_details = razorpay_client.refund_payment(
                transaction.razorpay_payment_id,
                refund_paise
            )
            
            # Update transaction
            transaction.refund_amount = refund_amount
            transaction.refund_id = refund_details["id"]
            transaction.refund_status = refund_details["status"]
            transaction.refund_reason = request.reason
            transaction.status = "refunded"
            transaction.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return RefundResponse(
                success=True,
                refund_id=refund_details["id"],
                transaction_id=transaction.transaction_id,
                refund_amount=refund_amount,
                status=RefundStatus.COMPLETED if refund_details["status"] == "processed" else RefundStatus.PROCESSING,
                message="Refund processed successfully",
                gateway_response=refund_details
            )
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Refund failed: {str(e)}")
    
    def get_transaction_history(self, request: TransactionHistoryRequest) -> List[Dict[str, Any]]:
        """
        Get transaction history with filters.
        
        Args:
            request: Transaction history request
            
        Returns:
            List of transactions
        """
        try:
            query = self.db.query(PaymentTransaction)
            
            # Apply filters
            if request.user_id:
                query = query.filter(PaymentTransaction.user_id == request.user_id)
            
            if request.order_id:
                query = query.filter(PaymentTransaction.order_id == request.order_id)
            
            if request.status:
                query = query.filter(PaymentTransaction.status == request.status.value)
            
            if request.payment_method:
                query = query.filter(PaymentTransaction.payment_method == request.payment_method.value)
            
            if request.from_date:
                query = query.filter(PaymentTransaction.created_at >= request.from_date)
            
            if request.to_date:
                query = query.filter(PaymentTransaction.created_at <= request.to_date)
            
            # Apply pagination
            transactions = query.order_by(
                PaymentTransaction.created_at.desc()
            ).offset(request.skip).limit(request.limit).all()
            
            return [
                {
                    "transaction_id": t.transaction_id,
                    "order_id": t.order_id,
                    "user_id": t.user_id,
                    "amount": float(t.amount),
                    "currency": t.currency,
                    "status": t.status,
                    "payment_method": t.payment_method,
                    "created_at": t.created_at,
                    "completed_at": t.completed_at,
                    "refund_amount": float(t.refund_amount) if t.refund_amount else None,
                    "refund_status": t.refund_status
                }
                for t in transactions
            ]
            
        except Exception as e:
            raise Exception(f"Failed to get transaction history: {str(e)}")
    
    def get_available_payment_methods(self) -> List[Dict[str, Any]]:
        """
        Get available payment methods.
        
        Returns:
            List of available payment methods
        """
        try:
            methods = [
                {
                    "name": "razorpay",
                    "display_name": "Razorpay",
                    "is_active": True,
                    "supported_currencies": ["INR"],
                    "min_amount": Decimal("1.00"),
                    "max_amount": Decimal("100000.00")
                }
            ]
            
            return methods
            
        except Exception as e:
            raise Exception(f"Failed to get payment methods: {str(e)}")
    
    def process_webhook_event(self, webhook_data: Dict[str, Any]) -> bool:
        """
        Process webhook event from Razorpay.
        
        Args:
            webhook_data: Webhook event data
            
        Returns:
            True if processed successfully
        """
        try:
            # Log webhook event
            webhook_event = WebhookEvent(
                gateway="razorpay",
                event_type=webhook_data.get("event", ""),
                event_id=webhook_data.get("id"),
                payload=webhook_data,
                processed=False
            )
            
            self.db.add(webhook_event)
            self.db.flush()
            
            # Parse event
            razorpay_client = get_razorpay_client()
            event_info = razorpay_client.parse_webhook_event(webhook_data)
            
            # Process based on event type
            if event_info["event_type"] == "payment.captured":
                self._handle_payment_captured(event_info)
            elif event_info["event_type"] == "payment.failed":
                self._handle_payment_failed(event_info)
            elif event_info["event_type"] == "refund.processed":
                self._handle_refund_processed(event_info)
            
            # Mark webhook as processed
            webhook_event.processed = True
            webhook_event.processed_at = datetime.utcnow()
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            # Mark webhook as failed
            if 'webhook_event' in locals():
                webhook_event.processing_error = str(e)
                self.db.commit()
            raise Exception(f"Webhook processing failed: {str(e)}")
    
    def _handle_payment_captured(self, event_info: Dict[str, Any]):
        """Handle payment captured webhook event."""
        try:
            # Find transaction by Razorpay payment ID
            transaction = self.db.query(PaymentTransaction).filter(
                PaymentTransaction.razorpay_payment_id == event_info.get("payment_id")
            ).first()
            
            if transaction and transaction.status == "pending":
                transaction.status = "completed"
                transaction.completed_at = datetime.utcnow()
                transaction.gateway_response = event_info
                self.db.commit()
                
        except Exception as e:
            raise Exception(f"Failed to handle payment captured: {str(e)}")
    
    def _handle_payment_failed(self, event_info: Dict[str, Any]):
        """Handle payment failed webhook event."""
        try:
            # Find transaction by Razorpay payment ID
            transaction = self.db.query(PaymentTransaction).filter(
                PaymentTransaction.razorpay_payment_id == event_info.get("payment_id")
            ).first()
            
            if transaction and transaction.status == "pending":
                transaction.status = "failed"
                transaction.gateway_response = event_info
                self.db.commit()
                
        except Exception as e:
            raise Exception(f"Failed to handle payment failed: {str(e)}")
    
    def _handle_refund_processed(self, event_info: Dict[str, Any]):
        """Handle refund processed webhook event."""
        try:
            # Find transaction by refund ID
            transaction = self.db.query(PaymentTransaction).filter(
                PaymentTransaction.refund_id == event_info.get("refund_id")
            ).first()
            
            if transaction:
                transaction.refund_status = "completed"
                transaction.gateway_response = event_info
                self.db.commit()
                
        except Exception as e:
            raise Exception(f"Failed to handle refund processed: {str(e)}")
