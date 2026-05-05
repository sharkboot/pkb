from fastapi import APIRouter, Body, Path, Query
from uuid import UUID
from typing import Optional
from models.schemas import BaseResponse, KnowledgeCreateRequest, KnowledgeUpdateRequest
from services.knowledge_service import KnowledgeService

router = APIRouter()
knowledge_service = KnowledgeService()


@router.get("/knowledge", response_model=BaseResponse)
async def list_knowledge(
    category: str = Query(None),
    keyword: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    knowledge_list, total = await knowledge_service.list_knowledge(category, keyword, page, page_size)
    return BaseResponse(data={
        "list": [k.dict() for k in knowledge_list],
        "total": total,
        "page": page,
        "pageSize": page_size,
    })


@router.get("/knowledge/search", response_model=BaseResponse)
async def search_knowledge(
    keyword: str = Query(...),
    category: str = Query(None),
    use_catalog: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """基于目录的两阶段搜索"""
    results, total, catalog_entries = await knowledge_service.search_knowledge(
        keyword, category, use_catalog, page, page_size
    )
    return BaseResponse(data={
        "list": [k.dict() for k in results],
        "total": total,
        "page": page,
        "pageSize": page_size,
        "catalogEntries": [
            {
                "id": str(e.id),
                "title": e.title,
                "summary": e.summary,
                "contentPreview": e.content_preview,
                "tags": e.tags,
                "category": e.category,
                "filePath": e.file_path,
                "status": e.status.value,
                "updatedAt": e.updated_at.isoformat(),
            }
            for e in catalog_entries
        ],
    })


@router.post("/knowledge/smart-search", response_model=BaseResponse)
async def smart_search(
    query: str = Body(..., embed=True),
):
    """智能搜索：把用户查询和目录一起给模型，让模型筛选相关条目"""
    result = await knowledge_service.smart_search(query)
    return BaseResponse(data={
        "query": result["query"],
        "reason": result["reason"],
        "relevantIds": result["relevantIds"],
        "results": [k.dict() for k in result["results"]],
        "total": result["total"],
    })


@router.get("/knowledge/catalog", response_model=BaseResponse)
async def get_catalog(
    keyword: str = Query(None),
    category: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """获取目录索引（快速浏览）"""
    catalog_entries = await knowledge_service.search_catalog(keyword, category, limit)
    return BaseResponse(data={
        "entries": [
            {
                "id": str(e.id),
                "title": e.title,
                "summary": e.summary,
                "contentPreview": e.content_preview[:100] + "..." if len(e.content_preview) > 100 else e.content_preview,
                "tags": e.tags,
                "category": e.category,
                "filePath": e.file_path,
                "status": e.status.value,
                "updatedAt": e.updated_at.isoformat(),
            }
            for e in catalog_entries
        ]
    })


@router.post("/knowledge/catalog/rebuild", response_model=BaseResponse)
async def rebuild_catalog():
    """重建目录索引"""
    count = await knowledge_service.rebuild_catalog()
    return BaseResponse(data={"count": count})

@router.post("/knowledge", response_model=BaseResponse)
async def create_knowledge(request: KnowledgeCreateRequest = Body(...)):
    knowledge = await knowledge_service.create_knowledge(request)
    return BaseResponse(data=knowledge.dict())

@router.get("/knowledge/{knowledge_id}", response_model=BaseResponse)
async def get_knowledge(knowledge_id: UUID = Path(...)):
    knowledge = await knowledge_service.get_knowledge(knowledge_id)
    return BaseResponse(data=knowledge.dict())

@router.put("/knowledge/{knowledge_id}", response_model=BaseResponse)
async def update_knowledge(
    knowledge_id: UUID = Path(...),
    request: KnowledgeUpdateRequest = Body(...),
):
    knowledge = await knowledge_service.update_knowledge(knowledge_id, request)
    return BaseResponse(data=knowledge.dict())

@router.delete("/knowledge/{knowledge_id}", response_model=BaseResponse)
async def delete_knowledge(knowledge_id: UUID = Path(...)):
    success = await knowledge_service.delete_knowledge(knowledge_id)
    return BaseResponse(data={"success": success})

@router.post("/knowledge/{knowledge_id}/star", response_model=BaseResponse)
async def star_knowledge(knowledge_id: UUID = Path(...)):
    knowledge = await knowledge_service.star_knowledge(knowledge_id)
    return BaseResponse(data=knowledge.dict())

@router.post("/knowledge/{knowledge_id}/restore", response_model=BaseResponse)
async def restore_knowledge(knowledge_id: UUID = Path(...)):
    knowledge = await knowledge_service.restore_knowledge(knowledge_id)
    return BaseResponse(data=knowledge.dict())

@router.delete("/knowledge/{knowledge_id}/permanent", response_model=BaseResponse)
async def permanent_delete(knowledge_id: UUID = Path(...)):
    success = await knowledge_service.permanent_delete(knowledge_id)
    return BaseResponse(data={"success": success})