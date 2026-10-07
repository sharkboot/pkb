"""Agent service for automatic content collection and multimodal understanding.

Handles:
- Webhook processing from external sources (Twitter, RSS, Slack, etc.)
- Scheduled crawling with configurable intervals
- Multimodal content parsing (images, PDFs)
- Integration with existing content pipeline
"""
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from services.content_service import ContentService
from models.schemas import ContentCollectRequest, KnowledgeUnit
from models.enums import SourceType
from llm.provider import chat_completion_with_images
from services.web_service import fetch_web_content

logger = logging.getLogger(__name__)


class AgentService:
    """Service for automatic content collection via webhooks and scheduled tasks."""

    def __init__(self):
        self.content_service = ContentService()
        self._configs: Dict[str, dict] = {}  # source_name -> config
        self._load_configs()

    def _load_configs(self):
        """Load agent configurations from file."""
        import os
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "..", "agent_configs.json"
        )
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self._configs = json.load(f)
                logger.info(f"Loaded {len(self._configs)} agent configurations")
            except Exception as e:
                logger.warning(f"Failed to load agent configs: {e}")

    def _save_configs(self):
        """Save agent configurations to file."""
        import os
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "..", "agent_configs.json"
        )
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self._configs, f, indent=2, ensure_ascii=False)

    async def handle_webhook(
        self,
        source: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process webhook payload and create knowledge items.

        Args:
            source: Source identifier (twitter, rss, slack, etc.)
            payload: Raw payload data from external service
            secret: Optional secret for verification

        Returns:
            Dict with result details
        """
        # Verify secret if provided
        if secret:
            stored_secret = self._configs.get(source, {}).get("secret")
            if stored_secret and stored_secret != secret:
                return {
                    "success": False,
                    "error": "Invalid webhook secret",
                    "source": source,
                }

        # Parse payload based on source type
        try:
            if source == "twitter":
                result = await self._process_twitter(payload)
            elif source == "rss":
                result = await self._process_rss(payload)
            elif source == "slack":
                result = await self._process_slack(payload)
            elif source == "webhook":
                result = await self._process_generic_webhook(payload)
            else:
                result = await self._process_generic(payload)

            return {
                "success": True,
                "source": source,
                "processed_at": datetime.now().isoformat(),
                "result": result,
            }

        except Exception as e:
            logger.error(f"Failed to process webhook from {source}: {e}")
            return {
                "success": False,
                "error": str(e),
                "source": source,
                "processed_at": datetime.now().isoformat(),
            }

    async def _process_twitter(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Twitter webhook payload."""
        tweet_text = payload.get("text", "")
        media_urls = payload.get("media", [])
        user = payload.get("user", {}).get("screen_name", "unknown")

        # Create content request
        request = ContentCollectRequest(
            source_type=SourceType.AGENT,
            content=tweet_text,
            images=media_urls if media_urls else None,
            metadata={
                "source": "twitter",
                "author": user,
                "original_url": payload.get("url"),
            },
        )

        knowledge = await self.content_service.collect(request)
        return {
            "knowledge_id": str(knowledge.id),
            "title": knowledge.title,
            "source": "twitter",
        }

    async def _process_rss(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process RSS feed payload."""
        items = payload.get("items", [])
        results = []

        for item in items[:10]:  # Limit to 10 items per webhook
            request = ContentCollectRequest(
                source_type=SourceType.AGENT,
                content=item.get("content", item.get("summary", "")),
                metadata={
                    "source": "rss",
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "published": item.get("published"),
                },
            )

            knowledge = await self.content_service.collect(request)
            results.append({
                "knowledge_id": str(knowledge.id),
                "title": knowledge.title,
            })

        return {
            "total_processed": len(results),
            "items": results,
        }

    async def _process_slack(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Slack webhook payload."""
        text = payload.get("text", "")
        attachments = payload.get("attachments", [])

        # Combine text and attachments
        full_content = text
        for attachment in attachments:
            if attachment.get("text"):
                full_content += f"\n\n{attachment['text']}"
            if attachment.get("title"):
                full_content += f"\n\n**{attachment['title']}**"

        request = ContentCollectRequest(
            source_type=SourceType.AGENT,
            content=full_content,
            metadata={
                "source": "slack",
                "channel": payload.get("channel_name"),
                "user": payload.get("user_name"),
            },
        )

        knowledge = await self.content_service.collect(request)
        return {
            "knowledge_id": str(knowledge.id),
            "title": knowledge.title,
            "channel": payload.get("channel_name"),
        }

    async def _process_generic_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process generic webhook payload."""
        content = payload.get("content", "")
        title = payload.get("title", "")
        url = payload.get("url", "")

        if url:
            # Try to fetch content from URL
            web_data = await fetch_web_content(url)
            if web_data:
                title = title or web_data.get("title", "Untitled")
                content = web_data.get("content", content)

        if not content:
            content = json.dumps(payload, ensure_ascii=False, indent=2)

        request = ContentCollectRequest(
            source_type=SourceType.AGENT,
            content=content,
            title=title,
            metadata=payload.get("metadata", {}),
        )

        knowledge = await self.content_service.collect(request)
        return {
            "knowledge_id": str(knowledge.id),
            "title": knowledge.title,
        }

    async def _process_generic(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process generic webhook payload."""
        content = payload.get("content", json.dumps(payload, ensure_ascii=False))
        title = payload.get("title", payload.get("subject", "Untitled"))

        request = ContentCollectRequest(
            source_type=SourceType.AGENT,
            content=content,
            title=title,
            metadata=payload.get("metadata", {}),
        )

        knowledge = await self.content_service.collect(request)
        return {
            "knowledge_id": str(knowledge.id),
            "title": knowledge.title,
        }

    async def crawl_url(self, url: str, interval_minutes: int = 60) -> Dict[str, Any]:
        """Schedule crawling of a URL with specified interval.

        Args:
            url: URL to crawl
            interval_minutes: How often to crawl (default 60 minutes)

        Returns:
            Configuration ID for tracking
        """
        config_id = hashlib.md5(url.encode()).hexdigest()[:8]

        self._configs[config_id] = {
            "url": url,
            "interval_minutes": interval_minutes,
            "enabled": True,
            "last_crawled": None,
            "created_at": datetime.now().isoformat(),
        }
        self._save_configs()

        return {
            "config_id": config_id,
            "url": url,
            "interval_minutes": interval_minutes,
        }

    def get_configs(self) -> List[Dict[str, Any]]:
        """Get all agent configurations."""
        return list(self._configs.values())

    def update_config(self, config_id: str, updates: Dict[str, Any]) -> bool:
        """Update an agent configuration."""
        if config_id in self._configs:
            self._configs[config_id].update(updates)
            self._save_configs()
            return True
        return False

    def delete_config(self, config_id: str) -> bool:
        """Delete an agent configuration."""
        if config_id in self._configs:
            del self._configs[config_id]
            self._save_configs()
            return True
        return False