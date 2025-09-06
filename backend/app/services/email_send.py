import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import get_settings
from .store import get_email, mark_status
from datetime import datetime

def send_email_reply(email_id: str, draft_content: str) -> dict:
    """Send email reply using SMTP and update email status"""
    settings = get_settings()
    
    if not all([settings.smtp_host, settings.smtp_user, settings.smtp_password]):
        return {"success": False, "error": "SMTP credentials not configured"}
    
    # Get original email details
    email_doc = get_email(email_id)
    if not email_doc:
        return {"success": False, "error": "Email not found"}
    
    sender_email = email_doc.get('sender', '')
    original_subject = email_doc.get('subject', '')
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.smtp_user
        msg['To'] = sender_email
        msg['Subject'] = f"Re: {original_subject}"
        
        # Add reply content
        text_part = MIMEText(draft_content, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # Send via SMTP
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        
        server.send_message(msg)
        server.quit()
        
        # Update email status to 'responded'
        mark_status(email_id, 'responded')
        
        # Update with response timestamp
        from .store import EMAILS
        if email_id in EMAILS:
            EMAILS[email_id]['responded_at'] = datetime.utcnow().isoformat()
            EMAILS[email_id]['response_sent'] = True
        
        return {
            "success": True, 
            "message": f"Reply sent successfully to {sender_email}",
            "sent_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to send email: {str(e)}"}


def send_bulk_replies(priority_filter: str = None) -> dict:
    """Send replies to multiple emails based on priority"""
    from .store import EMAILS
    
    sent_count = 0
    failed_count = 0
    errors = []
    
    for email_id, email_doc in EMAILS.items():
        # Skip if already responded
        if email_doc.get('status') == 'responded':
            continue
            
        # Filter by priority if specified
        if priority_filter and email_doc.get('priority') != priority_filter:
            continue
            
        # Check if draft exists
        from .store import RESPONSES
        draft = None
        for response in RESPONSES.values():
            if response['email_id'] == email_id and not response.get('final', False):
                draft = response['draft']
                break
                
        if not draft:
            continue
            
        # Send reply
        result = send_email_reply(email_id, draft)
        if result['success']:
            sent_count += 1
        else:
            failed_count += 1
            errors.append(f"{email_id}: {result['error']}")
    
    return {
        "sent": sent_count,
        "failed": failed_count,
        "errors": errors
    }
