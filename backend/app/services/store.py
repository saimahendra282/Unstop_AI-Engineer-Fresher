from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime, timedelta
import uuid

# In-memory store for demo (optionally persist to JSON later)
EMAILS: Dict[str, Dict[str, Any]] = {}
RESPONSES: Dict[str, Dict[str, Any]] = {}


def clear_all_data():
    """Clear all stored emails and responses - useful for testing"""
    global EMAILS, RESPONSES
    EMAILS.clear()
    RESPONSES.clear()
    return {"cleared_emails": True, "cleared_responses": True}


def upsert_email(doc: Dict[str, Any]) -> str:
    eid = doc.get('id') or doc.get('_id') or str(uuid.uuid4())
    doc['id'] = eid
    EMAILS[eid] = doc
    return eid


def list_emails_sorted(limit: int = 50) -> List[Dict[str, Any]]:
    return sorted(EMAILS.values(), key=lambda d: d.get('priority_score', 0), reverse=True)[:limit]


def get_email(eid: str) -> Dict[str, Any] | None:
    return EMAILS.get(eid)


def mark_status(eid: str, status: str):
    if eid in EMAILS:
        EMAILS[eid]['status'] = status


def add_response(email_id: str, draft: str, model: str = 'placeholder') -> str:
    rid = str(uuid.uuid4())
    RESPONSES[rid] = {
        'id': rid,
        'email_id': email_id,
        'draft': draft,
        'model': model,
        'created_at': datetime.utcnow().isoformat(),
        'final': False
    }
    return rid


def compute_stats():
    now = datetime.utcnow()
    last24 = now - timedelta(hours=24)
    emails = list(EMAILS.values())
    
    total_24 = 0
    for e in emails:
        received_str = e.get('received_at')
        if received_str and isinstance(received_str, str):
            try:
                received_dt = datetime.fromisoformat(received_str.replace('Z', '+00:00'))
                if received_dt >= last24:
                    total_24 += 1
            except (ValueError, TypeError):
                continue
    
    urgent = sum(1 for e in emails if e.get('priority') == 'urgent')
    responded = sum(1 for e in emails if e.get('status') == 'responded')
    pending = sum(1 for e in emails if e.get('status') != 'responded')
    
    # Calculate response time for responded emails
    response_times = []
    for e in emails:
        if e.get('status') == 'responded' and e.get('responded_at'):
            try:
                received_dt = datetime.fromisoformat(e.get('received_at', '').replace('Z', '+00:00'))
                responded_dt = datetime.fromisoformat(e.get('responded_at', '').replace('Z', '+00:00'))
                diff_minutes = (responded_dt - received_dt).total_seconds() / 60
                response_times.append(diff_minutes)
            except (ValueError, TypeError):
                continue
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else None
    
    sentiment_counts = {}
    for e in emails:
        s = e.get('sentiment', 'neutral')
        sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
    
    return {
        'total_last_24h': total_24,
        'urgent': urgent,
        'responded': responded,
        'pending': pending,
        'sentiment_counts': sentiment_counts,
        'avg_response_time_minutes': round(avg_response_time, 2) if avg_response_time else None,
        'total_emails': len(emails)
    }
