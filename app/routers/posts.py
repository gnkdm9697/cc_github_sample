import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.post import Post
from ..models.user import User
from ..schemas.post import PostResponse, PostCreate
from ..auth.auth import get_current_active_user

router = APIRouter()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/posts", response_model=PostResponse)
async def create_post(
    caption: str = Form(None),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Validate image file
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save image file
    file_extension = os.path.splitext(image.filename)[1]
    filename = f"{current_user.id}_{image.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # Create post in database
    db_post = Post(
        user_id=current_user.id,
        caption=caption,
        image_url=f"/uploads/{filename}"
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return db_post

@router.get("/posts", response_model=List[PostResponse])
def get_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = db.query(Post).offset(skip).limit(limit).all()
    return posts

@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.get("/users/{user_id}/posts", response_model=List[PostResponse])
def get_user_posts(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = db.query(Post).filter(Post.user_id == user_id).offset(skip).limit(limit).all()
    return posts

@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    # Delete image file
    if os.path.exists(post.image_url.lstrip("/")):
        os.remove(post.image_url.lstrip("/"))
    
    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}