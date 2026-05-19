# app/main.py

from fastapi import FastAPI, Request

from app.config import settings
from app.github.webhooks import handle_github_webhook

app = FastAPI(title=settings.app_name)


@app.post("/webhooks/github")
async def github_webhook(request: Request):
    return await handle_github_webhook(request)
