from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ExtractionResult(BaseModel):
    phones: List[str] = []
    emails: List[str] = []
    key_phrases: List[str] = []
    sentiment: str | None = None
    urgency_reason: str | None = None

class EmailRecord(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    message_id: str
    sender: str
    subject: str
    body: str
    received_at: datetime
    sentiment: Optional[str] = None
    priority: Optional[str] = None
    priority_score: Optional[float] = None
    extraction: Optional[ExtractionResult] = None
    status: str = "new"  # new, processed, responded

class ResponseDraft(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    email_id: str
    draft: str
    model: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    final: bool = False

class Stats(BaseModel):
    total_last_24h: int
    urgent: int
    responded: int
    pending: int
    sentiment_counts: dict
    avg_response_time_minutes: Optional[float] = None
