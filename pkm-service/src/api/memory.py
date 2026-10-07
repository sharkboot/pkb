from fastapi import APIRouter, Body, Query, Path, HTTPException
from typing import Optional, List
from pydantic import BaseModel, Field

from services.memory_service import MemoryService, SummaryType
from services.scheduler_service import scheduler_service
from models.schemas import BaseResponse

router = APIRouter()
memory_service = MemoryService()


# ========== Request/Response Models ==========

class MergeRequest(BaseModel):
    source_ids: List[str] = Field(..., description="List of knowledge IDs to merge")
    auto_delete_duplicates: bool = Field(False, description="Whether to delete merged items after merge")


class ScheduleUpdateRequest(BaseModel):
    daily_enabled: Optional[bool] = None
    weekly_enabled: Optional[bool] = None
    monthly_enabled: Optional[bool] = None
    daily_time: Optional[str] = None  # Format: "HH:MM"
    weekly_day: Optional[int] = None  # 0=Monday, 6=Sunday
    weekly_time: Optional[str] = None
    monthly_day: Optional[int] = None  # 1-31
    monthly_time: Optional[str] = None


class IntegrationStatusResponse(BaseModel):
    last_merge_time: Optional[str] = None
    last_dedup_time: Optional[str] = None
    last_summary_time: Optional[str] = None
    daily_schedule_enabled: bool = False
    weekly_schedule_enabled: bool = False
    monthly_schedule_enabled: bool = False
    daily_schedule_time: str = "09:00"
    weekly_schedule_day: int = 0
    weekly_schedule_time: str = "09:00"
    monthly_schedule_day: int = 1
    monthly_schedule_time: str = "09:00"


class ScheduledJob(BaseModel):
    id: str
    next_run_time: Optional[str] = None
    trigger: str


class DuplicateGroup(BaseModel):
    representative_id: str
    representative_title: str
    duplicates: List[dict]


class DeduplicationResponse(BaseModel):
    checked_count: int = 0
    duplicate_groups: List[DuplicateGroup] = []
    removed_count: int = 0
    error: Optional[str] = None


# ========== API Routes ==========

@router.post("/memory/merge", response_model=BaseResponse)
async def merge_knowledge(request: MergeRequest = Body(...)):
    """
    Merge multiple knowledge items into one.
    
    - Finds similar content using LLM
    - Combines into a single structured knowledge
    - Optionally deletes source items after merge
    """
    result = await memory_service.merge_knowledge(
        source_ids=request.source_ids,
        auto_delete_duplicates=request.auto_delete_duplicates,
    )
    
    if result.error:
        return BaseResponse(code=1, message=result.error)
    
    return BaseResponse(
        data={
            "merged_count": result.merged_count,
            "deleted_count": result.deleted_count,
            "created_knowledge_id": str(result.created_knowledge.id) if result.created_knowledge else None,
            "merged_ids": result.merged_ids,
        }
    )


@router.post("/memory/deduplicate", response_model=BaseResponse)
async def deduplicate(
    threshold: float = Query(0.85, ge=0.5, le=1.0, description="Similarity threshold (0-1)"),
):
    """
    Find and analyze duplicate knowledge items.
    
    - Uses embedding similarity to detect duplicates
    - Returns groups of similar knowledge
    - Does not automatically delete items
    """
    result = await memory_service.deduplicate(threshold=threshold)
    
    if result.error:
        return BaseResponse(code=1, message=result.error)
    
    return BaseResponse(
        data={
            "checked_count": result.checked_count,
            "duplicate_groups": [
                {
                    "representative_id": g["representative_id"],
                    "representative_title": g["representative_title"],
                    "duplicates": g["duplicates"],
                }
                for g in result.duplicate_groups
            ],
            "removed_count": result.removed_count,
        }
    )


@router.post("/memory/summary/{summary_type}", response_model=BaseResponse)
async def generate_summary(
    summary_type: str = Path(
        ...,
        description="Summary type: daily, weekly, or monthly",
        pattern="^(daily|weekly|monthly)$"
    ),
    title: Optional[str] = Query(None, description="Custom title for the summary"),
):
    """
    Generate a periodic summary of knowledge.
    
    - daily: Summarizes knowledge from the last 24 hours
    - weekly: Summarizes knowledge from the last 7 days
    - monthly: Summarizes knowledge from the last 30 days
    """
    try:
        st = SummaryType(summary_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid summary type: {summary_type}")
    
    result = await memory_service.generate_summary(
        summary_type=st,
        title=title,
    )
    
    if result.error:
        return BaseResponse(code=1, message=result.error)
    
    return BaseResponse(
        data={
            "summary_id": result.summary_id,
            "summary_type": result.summary_type.value if result.summary_type else summary_type,
            "knowledge_count": result.knowledge_count,
            "content_preview": result.content[:500] if result.content else "",
        }
    )


@router.post("/memory/integrate", response_model=BaseResponse)
async def run_integration(
    include_summary: bool = Query(True, description="Whether to generate daily summary"),
):
    """
    Run full memory integration process.
    
    - Deduplication check
    - Auto relation building
    - Daily summary generation (optional)
    """
    result = await memory_service.run_integration(include_summary=include_summary)
    return BaseResponse(data=result)


@router.get("/memory/status", response_model=BaseResponse)
async def get_status():
    """
    Get memory integration status and schedule configuration.
    """
    status = await memory_service.get_status()
    
    return BaseResponse(
        data={
            "last_merge_time": status.last_merge_time.isoformat() if status.last_merge_time else None,
            "last_dedup_time": status.last_dedup_time.isoformat() if status.last_dedup_time else None,
            "last_summary_time": status.last_summary_time.isoformat() if status.last_summary_time else None,
            "daily_schedule_enabled": status.daily_schedule_enabled,
            "weekly_schedule_enabled": status.weekly_schedule_enabled,
            "monthly_schedule_enabled": status.monthly_schedule_enabled,
            "daily_schedule_time": status.daily_schedule_time,
            "weekly_schedule_day": status.weekly_schedule_day,
            "weekly_schedule_time": status.weekly_schedule_time,
            "monthly_schedule_day": status.monthly_schedule_day,
            "monthly_schedule_time": status.monthly_schedule_time,
        }
    )


@router.put("/memory/schedule", response_model=BaseResponse)
async def update_schedule(request: ScheduleUpdateRequest = Body(...)):
    """
    Update schedule configuration for memory integration.
    
    - Enable/disable daily/weekly/monthly summaries
    - Set execution times
    - Changes take effect immediately
    """
    status = await scheduler_service.update_schedule_and_restart(
        daily_enabled=request.daily_enabled,
        weekly_enabled=request.weekly_enabled,
        monthly_enabled=request.monthly_enabled,
        daily_time=request.daily_time,
        weekly_day=request.weekly_day,
        weekly_time=request.weekly_time,
        monthly_day=request.monthly_day,
        monthly_time=request.monthly_time,
    )
    
    return BaseResponse(
        data={
            "daily_schedule_enabled": status.daily_schedule_enabled,
            "weekly_schedule_enabled": status.weekly_schedule_enabled,
            "monthly_schedule_enabled": status.monthly_schedule_enabled,
            "daily_schedule_time": status.daily_schedule_time,
            "weekly_schedule_day": status.weekly_schedule_day,
            "weekly_schedule_time": status.weekly_schedule_time,
            "monthly_schedule_day": status.monthly_schedule_day,
            "monthly_schedule_time": status.monthly_schedule_time,
        }
    )


@router.get("/memory/schedule/jobs", response_model=BaseResponse)
async def get_scheduled_jobs():
    """
    Get list of currently scheduled jobs.
    """
    jobs = scheduler_service.get_scheduled_jobs()
    return BaseResponse(data={"jobs": jobs})


@router.post("/memory/schedule/jobs/{job_id}/run", response_model=BaseResponse)
async def trigger_job(job_id: str = Path(..., description="Job ID to trigger")):
    """
    Trigger a scheduled job to run immediately.
    """
    result = scheduler_service.run_job_now(job_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return BaseResponse(data=result)


@router.post("/memory/relations/{knowledge_id}", response_model=BaseResponse)
async def build_relations(
    knowledge_id: str = Path(..., description="Knowledge ID"),
    limit: int = Query(5, ge=1, le=20, description="Max number of relations to build"),
):
    """
    Automatically build relations for a knowledge item.

    - Finds similar knowledge using embeddings
    - Creates bidirectional links
    """
    result = await memory_service.build_relations(knowledge_id, limit=limit)

    if "error" in result:
        return BaseResponse(code=1, message=result["error"])

    return BaseResponse(data=result)


@router.post("/memory/score/{knowledge_id}", response_model=BaseResponse)
async def score_knowledge(knowledge_id: str = Path(..., description="Knowledge ID")):
    """Score a knowledge item based on access frequency, relations, and LLM importance."""
    from uuid import UUID
    try:
        knowledge = await memory_service.score_knowledge(UUID(knowledge_id))
        return BaseResponse(data={
            "id": str(knowledge.id),
            "score": knowledge.score,
            "status": knowledge.status.value,
        })
    except Exception as e:
        return BaseResponse(code=1, message=f"Failed to score: {str(e)}")


@router.post("/memory/score/all", response_model=BaseResponse)
async def score_all_knowledge():
    """Score all active knowledge items."""
    result = await memory_service.score_all()
    return BaseResponse(data=result)


@router.post("/memory/smart-forget", response_model=BaseResponse)
async def smart_forget(threshold: float = Query(0.3, ge=0.0, le=1.0)):
    """Archive knowledge with score below threshold."""
    result = await memory_service.smart_forget(threshold=threshold)
    return BaseResponse(data=result)


@router.post("/memory/promote-hot", response_model=BaseResponse)
async def promote_hot(threshold: float = Query(0.8, ge=0.0, le=1.0)):
    """Promote high-score knowledge to permanent notes."""
    result = await memory_service.promote_hot(threshold=threshold)
    return BaseResponse(data=result)
