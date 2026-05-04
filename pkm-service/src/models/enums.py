from enum import Enum

class SourceType(str, Enum):
    SCREENSHOT = "screenshot"
    TEXT = "text"
    WEB = "web"
    PDF = "pdf"
    IMAGE = "image"
    MANUAL = "manual"
    AGENT = "agent"

class KnowledgeStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class TaskType(str, Enum):
    OCR = "ocr"
    SUMMARY = "summary"
    MERGE = "merge"
    ARCHIVE = "archive"
    VECTOR_INDEX = "vector_index"
    DEDUPLICATION = "deduplication"