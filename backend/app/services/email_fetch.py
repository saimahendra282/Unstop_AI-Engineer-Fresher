import base64
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..config import get_settings
from .nlp import analyze_email
from .store import upsert_email

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
FILTER_KEYWORDS = ["support", "query", "request", "help"]


def _hash_message_id(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()


def _get_gmail_service():
    """Get authenticated Gmail service using OAuth2"""
    settings = get_settings()
    creds = None
    
    # Load existing token
    token_path = settings.gmail_token_path or "token.json"
    if Path(token_path).exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_path = settings.gmail_credentials_path or "credentials.json"
            if not Path(credentials_path).exists():
                return None, "Gmail credentials.json file not found. Please download it from Google Cloud Console."
            
            # Check if it's the correct type of credentials
            try:
                with open(credentials_path, 'r') as f:
                    cred_data = json.load(f)
                    
                # Check if it's a service account (wrong type)
                if cred_data.get('type') == 'service_account':
                    return None, "Invalid credentials: Service Account detected. Gmail API requires Desktop Application credentials for personal email access."
                
                # Check if it has the correct structure for installed app
                if 'installed' not in cred_data and 'web' not in cred_data:
                    return None, "Invalid credentials: Must be OAuth2 Desktop Application credentials, not Service Account."
                    
            except Exception as e:
                return None, f"Error reading credentials file: {e}"
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                return None, f"OAuth2 flow failed: {e}"
        
        # Save the credentials for the next run
        try:
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            return None, f"Failed to save token: {e}"
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service, None
    except Exception as e:
        return None, f"Failed to build Gmail service: {str(e)}"


def _decode_base64_safe(data: str) -> str:
    """Safely decode base64 URL-safe data"""
    try:
        # Add padding if needed
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        
        decoded_bytes = base64.urlsafe_b64decode(data)
        return decoded_bytes.decode('utf-8', errors='ignore')
    except Exception:
        return ""


def _extract_email_body(payload) -> str:
    """Extract text body from Gmail message payload"""
    body_parts = []
    
    def extract_text_parts(part):
        if part.get('mimeType') == 'text/plain':
            body_data = part.get('body', {}).get('data', '')
            if body_data:
                body_parts.append(_decode_base64_safe(body_data))
        elif part.get('mimeType') == 'text/html':
            # Fallback to HTML if no plain text
            body_data = part.get('body', {}).get('data', '')
            if body_data and not body_parts:  # Only if no plain text found
                body_parts.append(_decode_base64_safe(body_data))
        elif 'parts' in part:
            for subpart in part['parts']:
                extract_text_parts(subpart)
    
    extract_text_parts(payload)
    return '\n'.join(body_parts)[:10000]  # Limit body size


def fetch_from_gmail_inbox(limit: int | None = None) -> dict:
    """Fetch real emails from Gmail inbox using Gmail API"""
    settings = get_settings()
    
    service, error = _get_gmail_service()
    if error:
        return {"fetched": 0, "stored": 0, "reason": error}
    
    try:
        # Build search query for support-related emails
        query_parts = [f'subject:"{keyword}"' for keyword in FILTER_KEYWORDS]
        search_query = ' OR '.join(query_parts)
        
        # Get message IDs
        results = service.users().messages().list(
            userId='me',
            q=search_query,
            maxResults=limit or 50
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return {"fetched": 0, "stored": 0, "reason": "No support emails found"}
        
        fetched = 0
        stored = 0
        
        for message in messages:
            try:
                # Get full message details
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                payload = msg['payload']
                headers = {h['name']: h['value'] for h in payload.get('headers', [])}
                
                subject = headers.get('Subject', '').strip()
                sender = headers.get('From', '').strip()
                date_str = headers.get('Date', '')
                
                # Double-check subject filtering
                if not any(k.lower() in subject.lower() for k in FILTER_KEYWORDS):
                    continue
                
                # Extract message ID
                message_id = headers.get('Message-ID') or _hash_message_id(sender + subject)
                
                # Extract body
                body = _extract_email_body(payload)
                
                # Parse date
                received_at = datetime.now(timezone.utc)
                if date_str:
                    try:
                        from email.utils import parsedate_to_datetime
                        received_at = parsedate_to_datetime(date_str)
                        if received_at.tzinfo is None:
                            received_at = received_at.replace(tzinfo=timezone.utc)
                    except Exception:
                        pass
                
                fetched += 1
                
                # Analyze email
                analysis = analyze_email(subject, body, sender)
                
                # Store email
                email_data = {
                    "message_id": message_id,
                    "subject": subject,
                    "sender": sender,
                    "body": body,
                    "received_at": received_at,
                    "priority": analysis["priority"],
                    "sentiment": analysis["sentiment"],
                    "category": analysis["category"],
                    "status": "new"
                }
                
                if upsert_email(email_data):
                    stored += 1
                    
            except Exception as e:
                print(f"Error processing message {message.get('id', 'unknown')}: {e}")
                continue
        
        return {
            "fetched": fetched,
            "stored": stored,
            "reason": "success"
        }
        
    except HttpError as e:
        return {"fetched": 0, "stored": 0, "reason": f"Gmail API error: {e}"}
    except Exception as e:
        return {"fetched": 0, "stored": 0, "reason": f"Unexpected error: {e}"}
