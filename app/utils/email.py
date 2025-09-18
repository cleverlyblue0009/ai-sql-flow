import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
try:
    import aiosmtplib
    SMTP_AVAILABLE = True
except ImportError:
    SMTP_AVAILABLE = False
    aiosmtplib = None
try:
    from jinja2 import Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    Template = None
import logging

from ..database.config import settings

logger = logging.getLogger(__name__)


# Email templates
VERIFICATION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Verify Your Email - AI Data Platform</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .logo { font-size: 24px; font-weight: bold; color: #2563eb; }
        .button { display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; }
        .footer { margin-top: 30px; text-align: center; color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">AI Data Platform</div>
        </div>
        
        <h2>Welcome! Please verify your email address</h2>
        
        <p>Thank you for registering with AI Data Platform. To complete your registration, please verify your email address by clicking the button below:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ verification_url }}" class="button">Verify Email Address</a>
        </div>
        
        <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #2563eb;">{{ verification_url }}</p>
        
        <p><strong>This link will expire in 24 hours.</strong></p>
        
        <div class="footer">
            <p>If you didn't create an account with us, please ignore this email.</p>
            <p>&copy; 2024 AI Data Platform. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

PASSWORD_RESET_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reset Your Password - AI Data Platform</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .logo { font-size: 24px; font-weight: bold; color: #2563eb; }
        .button { display: inline-block; background-color: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; }
        .footer { margin-top: 30px; text-align: center; color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">AI Data Platform</div>
        </div>
        
        <h2>Password Reset Request</h2>
        
        <p>We received a request to reset your password for your AI Data Platform account. If you made this request, click the button below to reset your password:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ reset_url }}" class="button">Reset Password</a>
        </div>
        
        <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #dc2626;">{{ reset_url }}</p>
        
        <p><strong>This link will expire in 1 hour.</strong></p>
        
        <div class="footer">
            <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
            <p>&copy; 2024 AI Data Platform. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """Send email using SMTP"""
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.smtp_username
        message["To"] = to_email
        
        # Add text content if provided
        if text_content:
            text_part = MIMEText(text_content, "plain")
            message.attach(text_part)
        
        # Add HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Send email
        if SMTP_AVAILABLE:
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                start_tls=True,
                username=settings.smtp_username,
                password=settings.smtp_password,
            )
        else:
            logger.warning("aiosmtplib not available, email not sent")
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


async def send_verification_email(email: str, verification_token: str) -> bool:
    """Send email verification email"""
    
    # Create verification URL
    # In production, this should be your frontend URL
    verification_url = f"http://localhost:3000/verify-email?token={verification_token}"
    
    # Render template
    if JINJA2_AVAILABLE:
        template = Template(VERIFICATION_EMAIL_TEMPLATE)
        html_content = template.render(verification_url=verification_url)
    else:
        html_content = VERIFICATION_EMAIL_TEMPLATE.replace("{{ verification_url }}", verification_url)
    
    # Send email
    return await send_email(
        to_email=email,
        subject="Verify Your Email - AI Data Platform",
        html_content=html_content,
        text_content=f"Please verify your email by visiting: {verification_url}"
    )


async def send_password_reset_email(email: str, reset_token: str) -> bool:
    """Send password reset email"""
    
    # Create reset URL
    # In production, this should be your frontend URL
    reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
    
    # Render template
    if JINJA2_AVAILABLE:
        template = Template(PASSWORD_RESET_EMAIL_TEMPLATE)
        html_content = template.render(reset_url=reset_url)
    else:
        html_content = PASSWORD_RESET_EMAIL_TEMPLATE.replace("{{ reset_url }}", reset_url)
    
    # Send email
    return await send_email(
        to_email=email,
        subject="Reset Your Password - AI Data Platform",
        html_content=html_content,
        text_content=f"Reset your password by visiting: {reset_url}"
    )


async def send_welcome_email(email: str, full_name: str) -> bool:
    """Send welcome email after successful verification"""
    
    welcome_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Welcome to AI Data Platform</title>
    </head>
    <body>
        <h2>Welcome to AI Data Platform, {{ full_name }}!</h2>
        
        <p>Your account has been successfully verified and you're now ready to start using our AI-powered data cleaning and migration tools.</p>
        
        <p>Here's what you can do:</p>
        <ul>
            <li>Upload and analyze your data for quality issues</li>
            <li>Use AI-powered data cleaning suggestions</li>
            <li>Migrate databases with intelligent SQL translation</li>
            <li>Monitor your projects and jobs in real-time</li>
        </ul>
        
        <p>Get started by logging into your account and creating your first project.</p>
        
        <p>Best regards,<br>The AI Data Platform Team</p>
    </body>
    </html>
    """
    
    if JINJA2_AVAILABLE:
        template = Template(welcome_template)
        html_content = template.render(full_name=full_name)
    else:
        html_content = welcome_template.replace("{{ full_name }}", full_name)
    
    return await send_email(
        to_email=email,
        subject="Welcome to AI Data Platform!",
        html_content=html_content,
        text_content=f"Welcome to AI Data Platform, {full_name}! Your account is now ready to use."
    )


class EmailService:
    """Email service class for sending various types of emails"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def send_verification_email(self, email: str, verification_token: str) -> bool:
        """Send email verification email"""
        return await send_verification_email(email, verification_token)
    
    async def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        """Send password reset email"""
        return await send_password_reset_email(email, reset_token)
    
    async def send_welcome_email(self, email: str, full_name: str) -> bool:
        """Send welcome email"""
        return await send_welcome_email(email, full_name)
    
    async def send_alert_email(self, email: str, subject: str, message: str) -> bool:
        """Send alert email"""
        alert_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{subject} - AI Data Platform</title>
        </head>
        <body>
            <h2>Alert: {subject}</h2>
            <p>{message}</p>
            <p>Best regards,<br>The AI Data Platform Team</p>
        </body>
        </html>
        """
        
        return await send_email(
            to_email=email,
            subject=f"Alert: {subject}",
            html_content=alert_template,
            text_content=f"Alert: {subject}\n\n{message}"
        )
    
    async def send_notification_email(self, email: str, subject: str, message: str) -> bool:
        """Send notification email"""
        return await self.send_alert_email(email, subject, message)