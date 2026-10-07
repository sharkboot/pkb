from fastapi import APIRouter, Body, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional
from models.schemas import BaseResponse, ContentCollectRequest
from services.content_service import ContentService
from services.agent_service import AgentService

router = APIRouter()
content_service = ContentService()
agent_service = AgentService()


class WebhookRequest(BaseModel):
    """Webhook request for external content triggering."""
    source: str  # e.g., "twitter", "rss", "slack"
    payload: dict = Field(..., description="External payload data")
    secret: Optional[str] = None  # Optional auth secret


class AgentConfig(BaseModel):
    """Agent configuration for scheduled crawling."""
    url: str
    interval_minutes: int = 60
    enabled: bool = True
    source_type: str = "url"


@router.post("/content/collect", response_model=BaseResponse)
async def collect_content(request: ContentCollectRequest = Body(...)):
    knowledge = await content_service.collect(request)
    return BaseResponse(data=knowledge.dict())


@router.post("/content/webhook", response_model=BaseResponse)
async def webhook_collect(request: WebhookRequest = Body(...)):
    """Handle external webhook triggers for automatic content collection.

    Supports sources like Twitter, RSS feeds, Slack, etc.
    The agent service will parse the payload and create knowledge items.
    """
    result = await agent_service.handle_webhook(request.source, request.payload, request.secret)
    return BaseResponse(data=result)


@router.post("/content/webhook/verify", response_model=BaseResponse)
async def verify_webhook_secret(secret: str = Header(..., alias="X-Webhook-Secret")):
    """Verify webhook secret is valid."""
    if not secret or len(secret) < 32:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    return BaseResponse(data={"valid": True})