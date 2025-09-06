from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routes.emails import router as emails_router

settings = get_settings()

app = FastAPI(title="AI Communication Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(',')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(emails_router)

@app.get("/")
async def root():
    return {"service": "AI Communication Assistant", "docs": "/docs"}
