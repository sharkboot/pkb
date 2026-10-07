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


@router.get("/knowledge/fts/search", response_model=BaseResponse)
async def fts_search(
    q: str = Query(..., description="Search keyword"),
    category: str = Query(None),
    tags: str = Query(None, description="Comma-separated tag filter"),
    limit: int = Query(20, ge=1, le=100),
):
    """SQLite FTS5 full-text search — fast keyword + tag combined search."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    result = await knowledge_service.fts_search(q, category=category, tags=tag_list, limit=limit)
    return BaseResponse(data=result)


@router.post("/knowledge/fts/rebuild", response_model=BaseResponse)
async def fts_rebuild():
    """Rebuild FTS index from all knowledge in storage."""
    count = await knowledge_service.fts_rebuild()
    return BaseResponse(data={"count": count})


@router.get("/knowledge/fts/status", response_model=BaseResponse)
async def fts_status():
    count = await knowledge_service.fts_index_count()
    return BaseResponse(data={"indexed": count})


@router.post("/knowledge/semantic-search", response_model=BaseResponse)
async def semantic_search(
    query: str = Body(..., embed=True),
    category: str = Body(None, embed=True),
    limit: int = Body(10, embed=True),
):
    """Vector semantic search (Chroma). Falls back to keyword search when vector store is disabled."""
    result = await knowledge_service.semantic_search(query, category=category, limit=limit)
    return BaseResponse(data=result)


@router.post("/knowledge/vector/index-all", response_model=BaseResponse)
async def index_all_vectors():
    """Bulk re-index all active knowledge items into the vector store."""
    from storage.vector_storage import vector_storage
    from llm.provider import create_embedding
    result = await vector_storage.index_all(knowledge_service, create_embedding)
    return BaseResponse(data=result)


@router.get("/knowledge/vector/status", response_model=BaseResponse)
async def vector_store_status():
    """Get vector store status: enabled flag and current index count."""
    from storage.vector_storage import vector_storage
    count = await vector_storage.index_count()
    return BaseResponse(data={
        "enabled": vector_storage.enabled,
        "indexed": count,
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


@router.get("/knowledge/{knowledge_id}/versions", response_model=BaseResponse)
async def get_knowledge_versions(knowledge_id: UUID = Path(...)):
    """Get version history for a knowledge item."""
    versions = await knowledge_service.storage.get_versions(knowledge_id)
    return BaseResponse(data={"versions": versions})


@router.get("/knowledge/{knowledge_id}/versions/{version_id}", response_model=BaseResponse)
async def get_knowledge_version(
    knowledge_id: UUID = Path(...),
    version_id: str = Path(...),
):
    """Get a specific version of knowledge."""
    version = await knowledge_service.storage.get_version(knowledge_id, version_id)
    if not version:
        return BaseResponse(code=404, message="Version not found")
    return BaseResponse(data=version.dict())


@router.post("/knowledge/{knowledge_id}/restore/{version_id}", response_model=BaseResponse)
async def restore_knowledge_version(
    knowledge_id: UUID = Path(...),
    version_id: str = Path(...),
):
    """Restore knowledge to a specific version."""
    from models.schemas import KnowledgeUpdateRequest
    version = await knowledge_service.storage.get_version(knowledge_id, version_id)
    if not version:
        return BaseResponse(code=404, message="Version not found")

    updated = await knowledge_service.update_knowledge(
        knowledge_id,
        KnowledgeUpdateRequest(
            title=version.title,
            content=version.content,
            summary=version.summary,
            tags=version.tags,
            category=version.category,
        )
    )
    return BaseResponse(data={"restored_to_version": version_id, "knowledge": updated.dict()})


@router.get("/knowledge/graph", response_model=BaseResponse)
async def get_knowledge_graph():
    """Get knowledge graph data (nodes and edges) for visualization."""
    all_knowledge, _ = await knowledge_service.list_knowledge(
        page=1, page_size=500
    )

    # Build nodes and edges
    nodes = []
    edges = []
    seen_edges = set()

    for knowledge in all_knowledge:
        if knowledge.status.value in ("deleted", "archived"):
            continue

        node_id = str(knowledge.id)
        nodes.append({
            "id": node_id,
            "title": knowledge.title,
            "category": knowledge.category,
            "tags": knowledge.tags,
            "score": knowledge.score,
            "status": knowledge.status.value,
        })

        # Build edges from relations
        for related_id in knowledge.relations or []:
            edge_key = tuple(sorted([node_id, related_id]))
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append({
                    "source": edge_key[0],
                    "target": edge_key[1],
                })

    return BaseResponse(data={
        "nodes": nodes,
        "edges": edges,
        "total": len(nodes),
    })


@router.get("/knowledge/{knowledge_id}/versions", response_model=BaseResponse)
async def get_knowledge_versions(knowledge_id: UUID = Path(...)):
    """Get version history for a knowledge item."""
    versions = await knowledge_service.storage.get_versions(knowledge_id)
    return BaseResponse(data={"versions": versions})


@router.get("/knowledge/{knowledge_id}/versions/{version_id}", response_model=BaseResponse)
async def get_knowledge_version(
    knowledge_id: UUID = Path(...),
    version_id: str = Path(...),
):
    """Get a specific version of knowledge."""
    version = await knowledge_service.storage.get_version(knowledge_id, version_id)
    if not version:
        return BaseResponse(code=404, message="Version not found")
    return BaseResponse(data=version.dict())


@router.post("/knowledge/{knowledge_id}/restore/{version_id}", response_model=BaseResponse)
async def restore_knowledge_version(
    knowledge_id: UUID = Path(...),
    version_id: str = Path(...),
):
    """Restore knowledge to a specific version."""
    version = await knowledge_service.storage.get_version(knowledge_id, version_id)
    if not version:
        return BaseResponse(code=404, message="Version not found")

    from models.schemas import KnowledgeUpdateRequest
    updated = await knowledge_service.update_knowledge(
        knowledge_id,
        KnowledgeUpdateRequest(
            title=version.title,
            content=version.content,
            summary=version.summary,
            tags=version.tags,
            category=version.category,
        )
    )
    return BaseResponse(data={"restored_to_version": version_id, "knowledge": updated.dict()})