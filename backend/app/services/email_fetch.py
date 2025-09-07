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
from .store import upsert_email

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
FILTER_KEYWORDS = {
    "support": ["support", "customer support", "tech support", "help desk"],
    "query": ["query", "question", "inquiry", "ask", "clarification"],
    "request": ["request", "please", "need", "require", "can you"],
    "urgent": ["urgent", "asap", "immediately", "critical", "emergency", "priority"],
    "help": ["help", "assistance", "guide", "how to", "tutorial"],
    "billing": ["billing", "payment", "invoice", "refund", "charge"],
    "technical": ["error", "bug", "issue", "problem", "not working", "broken"],
    "account": ["account", "login", "password", "access", "profile"]
}


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


def fetch_from_gmail_inbox(limit: int | None = None, filter_category: str = "all") -> dict:
    """Fetch real emails from Gmail inbox using Gmail API with advanced filtering"""
    settings = get_settings()
    
    service, error = _get_gmail_service()
    if error:
        return {"fetched": 0, "stored": 0, "reason": error}
    
    try:
        # Build search query based on filter category
        if filter_category == "all":
            # Search for any support-related emails from all categories
            all_keywords = []
            for category_keywords in FILTER_KEYWORDS.values():
                all_keywords.extend(category_keywords[:2])  # Take first 2 keywords per category
            query_parts = [f'subject:"{keyword}"' for keyword in all_keywords[:15]]  # Limit query length
            search_query = ' OR '.join(query_parts)
        else:
            # Search for specific category
            if filter_category in FILTER_KEYWORDS:
                category_keywords = FILTER_KEYWORDS[filter_category]
                query_parts = [f'subject:"{keyword}"' for keyword in category_keywords]
                search_query = ' OR '.join(query_parts)
            else:
                return {"fetched": 0, "stored": 0, "reason": f"Invalid filter category: {filter_category}"}
        
        # ULTRA FRESH MODE: Get emails from the last few minutes! 🔥
        # Gmail's after: operator supports different formats, let's try the most recent
        from datetime import datetime, timedelta
        
        # Get FRESH emails naturally - no timestamp restrictions!
        # Just fetch emails in natural order (newest to oldest)
        final_query = f'in:inbox ({search_query})'
        
        print(f"FETCHING EMAILS: Getting 50 emails naturally ordered newest to oldest")
        
        print(f"Gmail Search Query: {final_query}")
        
        # Get message IDs (Gmail naturally returns newest first, get 50)
        results = service.users().messages().list(
            userId='me',
            q=final_query,
            maxResults=50  # Get 50 emails naturally ordered
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return {"fetched": 0, "stored": 0, "reason": f"No emails found for filter: {filter_category}"}
        
        print(f"Found {len(messages)} emails, processing in natural order (newest first)")
        
        fetched = 0
        stored = 0
        
        # Process each message in natural order (Gmail already sorts newest first)
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
                
                # Double-check filter match (Gmail search might be broad)
                if filter_category != "all":
                    category_keywords = FILTER_KEYWORDS.get(filter_category, [])
                    if not any(keyword.lower() in subject.lower() for keyword in category_keywords):
                        continue
                else:
                    # For "all" filter, check if subject contains any support keywords
                    all_keywords = []
                    for cat_keywords in FILTER_KEYWORDS.values():
                        all_keywords.extend(cat_keywords)
                    if not any(keyword.lower() in subject.lower() for keyword in all_keywords):
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
                
                # Show email info without time restrictions
                current_time = datetime.now(timezone.utc)
                time_diff = current_time - received_at
                print(f"Email found! From {received_at.strftime('%Y-%m-%d %H:%M:%S')} ({time_diff.total_seconds()//3600:.0f} hours ago)")
                
                fetched += 1
                
                # Determine matched category for this email
                matched_category = filter_category if filter_category != "all" else "general"
                if filter_category == "all":
                    # Find best matching category
                    for cat, keywords in FILTER_KEYWORDS.items():
                        if any(keyword.lower() in subject.lower() for keyword in keywords):
                            matched_category = cat
                            break
                
                # Analyze email using same simple analysis as CSV for consistency
                from .nlp import simple_sentiment, urgency, extract_info
                sent = simple_sentiment(body)
                urg, reason = urgency(body + ' ' + subject)
                phones, emails, phrases = extract_info(body)
                priority_score = (5 if urg == 'urgent' else 0) + (2 if sent == 'negative' else 0)
                
                # Create email data
                email_data = {
                    "message_id": message_id,
                    "subject": subject,
                    "sender": sender,
                    "body": body,
                    "received_at": received_at,
                    "sentiment": sent,
                    "priority": urg,
                    "priority_score": priority_score,
                    "matched_category": matched_category,
                    "extraction": {
                        "phones": phones,
                        "emails": emails,
                        "key_phrases": phrases,
                        "sentiment": sent,
                        "urgency_reason": reason
                    },
                    "status": "pending"
                }
                
                # Store email directly (Gmail already gives us newest first)
                if upsert_email(email_data):
                    stored += 1
                    print(f"Stored email from {received_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    
            except Exception as e:
                print(f"Error processing message {message.get('id', 'unknown')}: {e}")
                continue
        
        return {
            "fetched": fetched,
            "stored": stored,
            "filter_category": filter_category,
            "reason": "success"
        }
        
    except HttpError as e:
        return {"fetched": 0, "stored": 0, "reason": f"Gmail API error: {e}"}
    except Exception as e:
        return {"fetched": 0, "stored": 0, "reason": f"Unexpected error: {e}"}
