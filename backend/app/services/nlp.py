import re
from .store import EMAILS

URGENT_KEYWORDS = ["immediately", "urgent", "cannot access", "critical", "asap", "down", "failure"]
SENTIMENT_POS = {"great", "thanks", "thank you", "appreciate", "good", "love"}
SENTIMENT_NEG = {"angry", "frustrated", "bad", "issue", "problem", "unhappy", "disappointed", "cannot", "fail"}

PHONE_REGEX = re.compile(r"\b(?:\+?\d[\d\-(). ]{7,}\d)\b")
EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def simple_sentiment(text: str) -> str:
    t = text.lower()
    pos_hits = sum(1 for w in SENTIMENT_POS if w in t)
    neg_hits = sum(1 for w in SENTIMENT_NEG if w in t)
    if neg_hits > pos_hits and neg_hits > 0:
        return "negative"
    if pos_hits > neg_hits and pos_hits > 0:
        return "positive"
    return "neutral"


def urgency(text: str) -> tuple[str, str | None]:
    lower = text.lower()
    for kw in URGENT_KEYWORDS:
        if kw in lower:
            return "urgent", f"keyword:{kw}"
    return "not_urgent", None


def extract_info(text: str):
    phones = PHONE_REGEX.findall(text)
    emails = EMAIL_REGEX.findall(text)
    # naive key phrases: top unique words length>4 limited
    words = re.findall(r"[A-Za-z]{5,}", text.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    key_phrases = [w for w, c in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]]
    return phones, emails, key_phrases


def analyze_email(subject: str, body: str, sender: str) -> dict:
    """Analyze email content and return analysis results"""
    sent = simple_sentiment(body)
    urgency_label, reason = urgency(body)
    phones, emails, key_phrases = extract_info(body)
    
    priority_score = 0.0
    if urgency_label == 'urgent':
        priority_score += 5
    if sent == 'negative':
        priority_score += 2
    priority_score += max(0, 1 - (len(body) / 5000))  # slight boost for shorter emails

    # Determine categories based on content
    categories = []
    subject_lower = subject.lower()
    body_lower = body.lower()
    
    if any(word in subject_lower + body_lower for word in ["account", "login", "password", "signin"]):
        categories.append("account")
    if any(word in subject_lower + body_lower for word in ["billing", "payment", "invoice", "refund"]):
        categories.append("billing")
    if any(word in subject_lower + body_lower for word in ["technical", "bug", "error", "not working"]):
        categories.append("technical")
    if any(word in subject_lower + body_lower for word in ["feature", "request", "suggestion"]):
        categories.append("feature_request")
    
    if not categories:
        categories.append("general")

    return {
        'sentiment': sent,
        'priority': urgency_label,
        'priority_score': priority_score,
        'urgency': urgency_label,
        'categories': categories,
        'extraction': {
            'phones': phones,
            'emails': emails,
            'key_phrases': key_phrases,
            'sentiment': sent,
            'urgency_reason': reason
        }
    }
