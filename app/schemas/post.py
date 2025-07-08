from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import User

class PostBase(BaseModel):
    caption: Optional[str] = None

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: int
    user_id: int
    image_url: str
    created_at: datetime
    updated_at: datetime
    user: User

    class Config:
        from_attributes = True

class PostResponse(BaseModel):
    id: int
    caption: Optional[str] = None
    image_url: str
    created_at: datetime
    user: User

    class Config:
        from_attributes = True