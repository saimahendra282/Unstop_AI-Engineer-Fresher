import csv
from datetime import datetime
from .nlp import simple_sentiment, urgency, extract_info
from .store import upsert_email

FILTER_KEYWORDS = ["support", "query", "request", "help"]


def load_csv(path: str) -> dict:
    count = 0
    stored = 0
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            count += 1
            subj = (row.get('subject') or '')
            if not any(k in subj.lower() for k in FILTER_KEYWORDS):
                continue
            body = row.get('body') or ''
            sent = simple_sentiment(body)
            urg, reason = urgency(body + ' ' + subj)
            phones, emails, phrases = extract_info(body)
            priority_score = (5 if urg == 'urgent' else 0) + (2 if sent == 'negative' else 0)
            # Parse date safely
            sent_date = row.get('sent_date', '')
            try:
                if sent_date and isinstance(sent_date, str):
                    received_at = datetime.fromisoformat(sent_date).isoformat()
                else:
                    received_at = datetime.now().isoformat()
            except (ValueError, TypeError):
                received_at = datetime.now().isoformat()
            
            doc = {
                'sender': row.get('sender') or '',
                'subject': subj,
                'body': body,
                'received_at': received_at,
                'sentiment': sent,
                'priority': urg,
                'priority_score': priority_score,
                'extraction': {
                    'phones': phones,
                    'emails': emails,
                    'key_phrases': phrases,
                    'sentiment': sent,
                    'urgency_reason': reason
                },
                'status': 'processed'
            }
            upsert_email(doc)
            stored += 1
    return {'rows': count, 'stored': stored}
