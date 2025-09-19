import os
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from googel_auth_manger import get_credentials

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class EmailAttachment:
    """Represents an email attachment"""
    filename: str
    content: bytes
    mime_type: str = 'application/octet-stream'

@dataclass
class EmailMessage:
    """Represents an email message"""
    to: str
    subject: str
    body: str
    cc: Optional[str] = None
    bcc: Optional[str] = None
    attachments: Optional[List[EmailAttachment]] = None
    is_html: bool = False

class GmailService:
    """Gmail API service for sending emails"""

    def __init__(self, credentials=None):
        self.service = None
        self.user_email = None
        self.credentials = credentials
        self._initialize_service()

    def _initialize_service(self):
        """Initialize the Gmail API service with authentication"""
        try:
            creds = self.credentials if self.credentials else get_credentials()
            self.service = build('gmail', 'v1', credentials=creds)

            # Get user profile to retrieve email address
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile['emailAddress']

            logger.info(f"Gmail service initialized successfully for {self.user_email}")

        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {str(e)}")
            raise

    def create_message(self, email_msg: EmailMessage) -> Dict[str, Any]:
        """Create a message for the Gmail API"""
        try:
            # Create message container
            if email_msg.attachments:
                message = MIMEMultipart()
            else:
                message = MIMEText(email_msg.body, 'html' if email_msg.is_html else 'plain')
                message['to'] = email_msg.to
                message['subject'] = email_msg.subject
                if email_msg.cc:
                    message['cc'] = email_msg.cc
                if email_msg.bcc:
                    message['bcc'] = email_msg.bcc
                message['from'] = self.user_email

                return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

            # Handle multipart message with attachments
            message['to'] = email_msg.to
            message['subject'] = email_msg.subject
            message['from'] = self.user_email
            if email_msg.cc:
                message['cc'] = email_msg.cc
            if email_msg.bcc:
                message['bcc'] = email_msg.bcc

            # Add body
            body_part = MIMEText(email_msg.body, 'html' if email_msg.is_html else 'plain')
            message.attach(body_part)

            # Add attachments
            if email_msg.attachments:
                for attachment in email_msg.attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.content)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment.filename}'
                    )
                    message.attach(part)

            return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

        except Exception as e:
            logger.error(f"Failed to create email message: {str(e)}")
            raise

    def send_email(self, email_msg: EmailMessage) -> Dict[str, Any]:
        """Send an email using Gmail API"""
        try:
            if not self.service:
                raise Exception("Gmail service not initialized")

            message = self.create_message(email_msg)

            result = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()

            logger.info(f"Email sent successfully. Message ID: {result['id']}")
            logger.info(f"Email sent to: {email_msg.to}")
            logger.info(f"Subject: {email_msg.subject}")

            return {
                'success': True,
                'message_id': result['id'],
                'recipient': email_msg.to,
                'subject': email_msg.subject
            }

        except HttpError as error:
            logger.error(f"Gmail API HTTP error: {error}")
            return {
                'success': False,
                'error': f"Gmail API error: {error}",
                'error_code': error.resp.status if error.resp else None
            }
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def send_simple_email(self, to: str, subject: str, body: str, is_html: bool = False) -> Dict[str, Any]:
        """Send a simple email without attachments"""
        email_msg = EmailMessage(
            to=to,
            subject=subject,
            body=body,
            is_html=is_html
        )
        return self.send_email(email_msg)

    def send_email_with_cc_bcc(self, to: str, subject: str, body: str,
                              cc: Optional[str] = None, bcc: Optional[str] = None,
                              is_html: bool = False) -> Dict[str, Any]:
        """Send an email with CC and BCC recipients"""
        email_msg = EmailMessage(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc,
            is_html=is_html
        )
        return self.send_email(email_msg)

    def get_user_profile(self) -> Dict[str, Any]:
        """Get the authenticated user's Gmail profile"""
        try:
            if not self.service:
                raise Exception("Gmail service not initialized")

            profile = self.service.users().getProfile(userId='me').execute()
            return {
                'success': True,
                'email': profile['emailAddress'],
                'messages_total': profile['messagesTotal'],
                'threads_total': profile['threadsTotal'],
                'history_id': profile['historyId']
            }
        except Exception as e:
            logger.error(f"Failed to get user profile: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def validate_email_format(self, email: str) -> bool:
        """Basic email format validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

# Global Gmail service instance
_gmail_service = None

def get_gmail_service() -> GmailService:
    """Get a singleton Gmail service instance"""
    global _gmail_service
    if _gmail_service is None:
        _gmail_service = GmailService()
    return _gmail_service

def send_email_quick(to: str, subject: str, body: str, is_html: bool = False) -> Dict[str, Any]:
    """Quick function to send an email"""
    try:
        service = get_gmail_service()
        return service.send_simple_email(to, subject, body, is_html)
    except Exception as e:
        logger.error(f"Quick send email failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }