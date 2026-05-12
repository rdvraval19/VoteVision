# app/main.py

from fastapi import FastAPI
from app.routers import elections, candidates, news, realtime

app = FastAPI(
    title="VoteVision — Election Intelligence Platform",
    description="AI-powered election monitoring, sentiment analysis, and fake news detection.",
    version="0.4.0",   # ← BUMP VERSION
)

app.include_router(elections.router)
app.include_router(candidates.router)
app.include_router(news.router)   # ← ADD THIS
app.include_router(realtime.router)

@app.get("/", tags=["Health"])
def root():
    return {
        "platform": "VoteVision",
        "status":   "online",
        "version":  "0.4.0",    # ← BUMP VERSION
        "message":  "Election Intelligence Platform is running.",
    }

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}