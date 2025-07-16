from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

# Pydantic models for request/response
class ContentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class ContentCreate(ContentBase):
    """Schema for creating new content"""
    pass

class ContentUpdate(BaseModel):
    """Schema for updating content"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = None
    container_id: Optional[str] = None
    internal_port: Optional[int] = None

class ContentInDBBase(ContentBase):
    """Base schema for content in the database"""
    id: int
    image_name: str
    status: str = "creating"
    container_id: Optional[str] = None
    internal_port: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Pydantic v2 style config
    model_config = ConfigDict(from_attributes=True)

class Content(ContentInDBBase):
    """Schema for content response"""
    pass

class ContentInDB(ContentInDBBase):
    """Schema for content in the database"""
    pass
