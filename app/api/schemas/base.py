from pydantic import BaseModel as BaseModel


class BaseAPISchema(BaseModel):
    """Base class for all API schemas"""
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class ResponseSchema(BaseModel):
    status: str = "success"
    message: str
