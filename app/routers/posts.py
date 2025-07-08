import os
import shutil
import uuid
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

# File upload constraints
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}

@router.post("/posts", response_model=PostResponse)
async def create_post(
    caption: str = Form(None),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Validate file size
    if image.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size too large (max 10MB)")
    
    # Validate file type
    if image.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed")
    
    # Validate file extension
    file_extension = os.path.splitext(image.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension")
    
    # Generate secure filename
    secure_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, secure_filename)
    
    try:
        # Save image file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        # Create post in database
        db_post = Post(
            user_id=current_user.id,
            caption=caption,
            image_url=f"/uploads/{secure_filename}"
        )
        db.add(db_post)
        db.commit()
        db.refresh(db_post)
        
        return db_post
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail="Failed to create post")

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
    
    # Safely delete image file
    if post.image_url:
        # Extract filename from URL (remove /uploads/ prefix)
        filename = post.image_url.replace("/uploads/", "")
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Ensure the file path is within the upload directory (prevent path traversal)
        if os.path.commonpath([UPLOAD_DIR, file_path]) == UPLOAD_DIR and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                # Log the error but don't fail the deletion
                pass
    
    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}