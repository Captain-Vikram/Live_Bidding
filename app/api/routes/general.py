from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.general import (
    SubscriberSchema,
    SiteDetailResponseSchema,
    SubscriberResponseSchema,
    ReviewsResponseSchema,
)
from app.core.database import get_db

from app.db.managers.general import (
    sitedetail_manager,
    subscriber_manager,
    review_manager,
)
from app.db.managers.base import file_manager
from app.api.utils.file_types import ALLOWED_IMAGE_TYPES

router = APIRouter()


@router.get(
    "/site-detail",
    summary="Retrieve site details",
    description="This endpoint retrieves few details of the site/application",
)
async def retrieve_site_details(
    db: AsyncSession = Depends(get_db),
) -> SiteDetailResponseSchema:
    sitedetail = await sitedetail_manager.get(db)
    return {"message": "Site Details fetched", "data": sitedetail}


@router.post(
    "/subscribe",
    summary="Add a subscriber",
    description="This endpoint creates a newsletter subscriber in our application",
    status_code=201,
)
async def subscribe(
    data: SubscriberSchema, db: AsyncSession = Depends(get_db)
) -> SubscriberResponseSchema:
    email = data.email
    subscriber = await subscriber_manager.get_by_email(db, email)
    if not subscriber:
        subscriber = await subscriber_manager.create(db, {"email": email})

    return {"message": "Subscription successful", "data": subscriber}


@router.get(
    "/reviews",
    summary="Retrieve site reviews",
    description="This endpoint retrieves a few reviews of the application",
)
async def reviews(db: AsyncSession = Depends(get_db)) -> ReviewsResponseSchema:
    reviews = await review_manager.get_active(db)
    return {"message": "Reviews fetched", "data": reviews}


@router.post(
    "/upload-image",
    summary="Upload image file",
    description="Upload an image file and get the file ID for use in listings or profile. Supports JPEG, PNG, WEBP formats.",
    status_code=201,
)
async def upload_image(
    file: UploadFile = File(..., description="Image file to upload"),
    db: AsyncSession = Depends(get_db),
):
    """Upload an image file and return the file ID"""
    
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file.content_type} not allowed. Supported types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # Validate file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="File size too large. Maximum allowed size is 5MB."
        )
    
    # Reset file pointer for potential future reading
    await file.seek(0)
    
    # Create file record in database
    file_data = {
        "resource_type": file.content_type,
        "filename": file.filename,
        "size": len(file_content)
    }
    
    db_file = await file_manager.create(db, file_data)
    
    return {
        "message": "Image uploaded successfully",
        "data": {
            "file_id": db_file.id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content)
        }
    }
