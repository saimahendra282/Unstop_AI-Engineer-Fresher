# AI-Powered Communication Assistant (Hackathon Skeleton)

## Overview
Scaffold for an AI-driven assistant to triage support emails: fetch, filter, analyze sentiment & urgency, extract structured info, prioritize, and draft responses (Gemini + RAG placeholders).

## Architecture
Backend: FastAPI (REST)  
DB: MongoDB collections (emails, responses, knowledge_chunks)  
NLP: Lightweight rule-based sentiment/urgency (upgradeable)  
RAG: (Planned) Markdown docs -> chunks -> embeddings (sentence-transformers) -> FAISS  
LLM: Gemini API (placeholder stub currently)  
UI: Streamlit dashboard (inbox + draft)

## Setup
1. (Optional) Python venv
2. Install deps:
```
pip install -r backend/requirements.txt
```
3. Copy environment template:
```
copy .env.example .env   # Windows PowerShell equivalent: Copy-Item .env.example .env
```
4. Edit `.env` with credentials (Mongo, IMAP, SMTP optional, GEMINI_API_KEY).

## Run Services
API:
```
uvicorn backend.app.main:app --reload
```
Dashboard:
```
streamlit run dashboard/app.py
```
Visit: http://localhost:8501

## Endpoints (current)
- GET /health
- POST /emails/fetch (fetch unseen & filter)
- GET /emails/ (list prioritized)
- GET /emails/{id}
- POST /emails/{id}/draft (placeholder draft generation)

## Enhancements To Build
- Gemini integration & prompt engineering
- RAG ingestion + retrieval (vector store persistence)
- Stats endpoint (24h metrics, sentiment distribution)
- SMTP send + response finalization
- Background scheduler / Celery or APScheduler
- Auth (API key / OAuth)
- Better sentiment (transformers / sentiment model)
- Proper parsing of Date header & time zones

## Data Model (simplified)
Email: message_id, sender, subject, body, received_at, sentiment, priority, priority_score, extraction{phones, emails, key_phrases, sentiment, urgency_reason}, status
Response: email_id, draft, model, created_at, final

## Disclaimer
Skeleton code for hackathon speed; hardening, error handling, logging, and security need expansion.
