from typing import List, Optional
from uuid import UUID
from uuid6 import uuid6
from datetime import datetime
from storage.markdown_storage import MarkdownStorage
from models.schemas import Category, CategoryCreateRequest
from models.exceptions import ResourceNotFoundException

class CategoryService:
    def __init__(self):
        self.storage = MarkdownStorage()

    async def create_category(self, request: CategoryCreateRequest) -> Category:
        now = datetime.now()
        category = Category(
            id=uuid6(),
            name=request.name,
            parent_id=request.parent_id,
            created_at=now,
            updated_at=now,
        )
        
        await self.storage.save_category(category)
        return category

    async def get_category(self, category_id: UUID) -> Category:
        category = await self.storage.get_category(category_id)
        if not category:
            raise ResourceNotFoundException(f"分类 {category_id} 不存在")
        return category

    async def list_categories(self) -> List[Category]:
        return await self.storage.list_categories()

    async def delete_category(self, category_id: UUID) -> bool:
        category = await self.storage.get_category(category_id)
        if not category:
            raise ResourceNotFoundException(f"分类 {category_id} 不存在")
        
        return await self.storage.delete_category(category_id)