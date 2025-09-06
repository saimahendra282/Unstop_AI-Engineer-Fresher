from fastapi import APIRouter
from ..services.csv_ingest import load_csv
from ..services.email_fetch import fetch_from_gmail_inbox
from ..services.store import list_emails_sorted, get_email, add_response
from ..services.response import generate_draft
from ..services.email_send import send_email_reply, send_bulk_replies
from ..config import get_settings
from ..services.store import compute_stats

router = APIRouter(prefix="/emails", tags=["emails"])

@router.post('/load_csv')
async def load_from_csv(path: str | None = None):
    settings = get_settings()
    return load_csv(path or settings.csv_path)

@router.post('/load_inbox')
async def load_from_inbox(limit: int = 50):
    """Load support emails from Gmail inbox using IMAP"""
    return fetch_from_gmail_inbox(limit=limit)

@router.get('/')
async def list_emails(limit: int = 50):
    docs = list_emails_sorted(limit=limit)
    return [{k: v for k, v in d.items() if k != 'body'} for d in docs]

@router.get('/{email_id}')
async def get_email_detail(email_id: str):
    doc = get_email(email_id)
    if not doc:
        return {"error": "not found"}
    return doc

@router.post('/{email_id}/draft')
async def make_draft(email_id: str):
    draft = generate_draft(email_id)
    if not draft:
        return {"error": "email not found"}
    # store response draft
    add_response(email_id, draft)
    return {"draft": draft}

@router.post('/{email_id}/send')
async def send_reply(email_id: str, draft: str = None):
    if not draft:
        # Use existing draft
        from ..services.store import RESPONSES
        for response in RESPONSES.values():
            if response['email_id'] == email_id and not response.get('final', False):
                draft = response['draft']
                break
        if not draft:
            return {"error": "No draft found. Generate a draft first."}
    
    result = send_email_reply(email_id, draft)
    return result

@router.post('/send_bulk')
async def send_bulk(priority_filter: str = None):
    """Send replies to multiple emails. priority_filter: 'urgent' or None for all"""
    result = send_bulk_replies(priority_filter)
    return result

@router.get('/stats')
async def stats():
    return compute_stats()
