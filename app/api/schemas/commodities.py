from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from uuid import UUID
from .base import ResponseSchema


class CommodityCreateSchema(BaseModel):
    commodity_name: str = Field(..., example="Wheat", max_length=100)
    description: Optional[str] = Field(None, example="High quality wheat harvested this season")
    quantity_kg: float = Field(..., example=1000.0, gt=0)
    harvest_date: date = Field(..., example="2025-01-15")
    min_price: float = Field(..., example=25.50, gt=0)
    closing_date: Optional[datetime] = Field(None, example="2025-08-01T12:00:00")
    category_id: Optional[str] = Field(None, example="123e4567-e89b-12d3-a456-426614174000")
    
    # Mandatory product image
    image_id: UUID = Field(..., example="123e4567-e89b-12d3-a456-426614174000", description="UUID of uploaded product image file (required)")

    @validator("harvest_date")
    def validate_harvest_date(cls, v):
        if v > date.today():
            raise ValueError("Harvest date cannot be in the future")
        return v

    @validator("closing_date")
    def validate_closing_date(cls, v):
        if v and v <= datetime.now():
            raise ValueError("Closing date must be in the future")
        return v


class CommodityUpdateSchema(BaseModel):
    commodity_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None)
    quantity_kg: Optional[float] = Field(None, gt=0)
    harvest_date: Optional[date] = Field(None)
    min_price: Optional[float] = Field(None, gt=0)
    closing_date: Optional[datetime] = Field(None)
    category_id: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)

    @validator("harvest_date")
    def validate_harvest_date(cls, v):
        if v and v > date.today():
            raise ValueError("Harvest date cannot be in the future")
        return v

    @validator("closing_date")
    def validate_closing_date(cls, v):
        if v and v <= datetime.now():
            raise ValueError("Closing date must be in the future")
        return v


class CommodityResponseSchema(BaseModel):
    id: str
    commodity_name: str
    description: Optional[str]
    quantity_kg: float
    harvest_date: date
    min_price: float
    highest_bid: float
    bids_count: int
    is_approved: bool
    is_active: bool
    closing_date: Optional[datetime]
    slug: str
    farmer: dict
    category: Optional[dict]
    image: Optional[dict]
    created_at: datetime
    updated_at: datetime
    time_left: Optional[float]

    class Config:
        from_attributes = True


class CommodityListResponseSchema(ResponseSchema):
    data: List[CommodityResponseSchema]


class CommodityDetailResponseSchema(ResponseSchema):
    data: CommodityResponseSchema


class CommodityApprovalSchema(BaseModel):
    is_approved: bool = Field(..., example=True)


class CommodityApprovalResponseSchema(ResponseSchema):
    data: dict = Field(default={"message": "Commodity approval status updated successfully"})
