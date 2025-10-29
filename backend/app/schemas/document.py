from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentBase(BaseModel):
    title: str
    filename: str
    document_type: Optional[str] = None


class DocumentCreate(DocumentBase):
    file_path: str
    content: Optional[str] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    document_type: Optional[str] = None
    is_processed: Optional[bool] = None
    vector_id: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: int
    file_path: str
    is_processed: bool
    vector_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
