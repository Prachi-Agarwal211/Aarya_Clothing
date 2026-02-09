"""Email service for sending emails via SMTP."""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

from core.config import settings


class EmailService:
    """Email service for sending emails via SMTP."""
    
    def __init__(self):
        """Initialize email service."""
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_TLS
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    def _create_message(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> MIMEMultipart:
        """Create email message."""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to_email
        
        # Add text version
        if text_content:
            part1 = MIMEText(text_content, "plain")
            message.attach(part1)
        
        # Add HTML version
        part2 = MIMEText(html_content, "html")
        message.attach(part2)
        
        return message
    
    def _send_sync(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email synchronously."""
        if not self.user or not self.password:
            print(f"[EMAIL] SMTP not configured. Would send to: {to_email}")
            print(f"[EMAIL] Subject: {subject}")
            return True  # Pretend success for development
        
        try:
            message = self._create_message(to_email, subject, html_content, text_content)
            
            context = ssl.create_default_context()
            
            if self.use_tls:
                with smtplib.SMTP(self.host, self.port) as server:
                    server.starttls(context=context)
                    server.login(self.user, self.password)
                    server.sendmail(self.from_email, to_email, message.as_string())
            else:
                with smtplib.SMTP_SSL(self.host, self.port, context=context) as server:
                    server.login(self.user, self.password)
                    server.sendmail(self.from_email, to_email, message.as_string())
            
            print(f"[EMAIL] Sent to: {to_email}")
            return True
            
        except Exception as e:
            print(f"[EMAIL] Failed to send to {to_email}: {str(e)}")
            return False
    
    async def send_async(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._send_sync,
            to_email,
            subject,
            html_content,
            text_content
        )
    
    def send(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email (synchronous wrapper)."""
        return self._send_sync(to_email, subject, html_content, text_content)
    
    # ==================== Email Templates ====================
    
    def send_password_reset_email(self, to_email: str, reset_token: str, reset_url: str) -> bool:
        """Send password reset email."""
        subject = "Reset Your Password - Aarya Clothings"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0E0E0E; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #1A1A1A; border-radius: 16px; padding: 40px; border: 1px solid rgba(212, 175, 55, 0.2);">
                <!-- Header -->
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #D4AF37; font-size: 28px; margin: 0; font-family: 'Playfair Display', serif;">Aarya Clothings</h1>
                </div>
                
                <!-- Content -->
                <div style="color: #F4EDE4; font-size: 16px; line-height: 1.6;">
                    <h2 style="color: #F4EDE4; font-size: 22px; margin-bottom: 20px;">Reset Your Password</h2>
                    
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    
                    <!-- Button -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="display: inline-block; background-color: #D4AF37; color: #000000; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">Reset Password</a>
                    </div>
                    
                    <p style="color: #B89C5A; font-size: 14px;">This link will expire in 24 hours.</p>
                    
                    <p style="color: #B89C5A; font-size: 14px;">If you didn't request a password reset, you can safely ignore this email.</p>
                    
                    <hr style="border: none; border-top: 1px solid rgba(212, 175, 55, 0.2); margin: 30px 0;">
                    
                    <p style="color: #B89C5A; font-size: 12px; text-align: center;">
                        If the button doesn't work, copy and paste this link into your browser:<br>
                        <a href="{reset_url}" style="color: #D4AF37; word-break: break-all;">{reset_url}</a>
                    </p>
                </div>
                
                <!-- Footer -->
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(212, 175, 55, 0.2);">
                    <p style="color: #B89C5A; font-size: 12px; margin: 0;">
                        © 2026 Aarya Clothings. All rights reserved.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Reset Your Password - Aarya Clothings
        
        We received a request to reset your password. 
        
        Click the link below to create a new password:
        {reset_url}
        
        This link will expire in 24 hours.
        
        If you didn't request a password reset, you can safely ignore this email.
        
        © 2026 Aarya Clothings
        """
        
        return self.send(to_email, subject, html_content, text_content)
    
    def send_otp_email(self, to_email: str, otp_code: str, purpose: str = "verification") -> bool:
        """Send OTP verification email."""
        subject = f"Your Verification Code - Aarya Clothings"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0E0E0E; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #1A1A1A; border-radius: 16px; padding: 40px; border: 1px solid rgba(212, 175, 55, 0.2);">
                <!-- Header -->
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #D4AF37; font-size: 28px; margin: 0; font-family: 'Playfair Display', serif;">Aarya Clothings</h1>
                </div>
                
                <!-- Content -->
                <div style="color: #F4EDE4; font-size: 16px; line-height: 1.6;">
                    <h2 style="color: #F4EDE4; font-size: 22px; margin-bottom: 20px;">Your Verification Code</h2>
                    
                    <p>Use the following code to complete your {purpose}:</p>
                    
                    <!-- OTP Code -->
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="display: inline-block; background-color: #0E0E0E; border: 2px solid #D4AF37; border-radius: 12px; padding: 20px 40px;">
                            <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #D4AF37;">{otp_code}</span>
                        </div>
                    </div>
                    
                    <p style="color: #B89C5A; font-size: 14px;">This code will expire in 10 minutes.</p>
                    
                    <p style="color: #B89C5A; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
                </div>
                
                <!-- Footer -->
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(212, 175, 55, 0.2);">
                    <p style="color: #B89C5A; font-size: 12px; margin: 0;">
                        © 2026 Aarya Clothings. All rights reserved.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Your Verification Code - Aarya Clothings
        
        Use the following code to complete your {purpose}:
        
        {otp_code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this code, please ignore this email.
        
        © 2026 Aarya Clothings
        """
        
        return self.send(to_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()
