from pydantic import BaseModel, validator, Field, EmailStr
from typing import Optional
from enum import Enum
from .base import ResponseSchema
from uuid import UUID


class UserRoleEnum(str, Enum):
    FARMER = "FARMER"
    TRADER = "TRADER"
    ADMIN = "ADMIN"


class RegisterUserSchema(BaseModel):
    first_name: str = Field(..., example="John", max_length=50)
    last_name: str = Field(..., example="Doe", max_length=50)
    email: EmailStr = Field(..., example="johndoe@example.com")
    password: str = Field(..., example="strongpassword", min_length=8)
    terms_agreement: bool
    
    # New agricultural fields
    role: UserRoleEnum = Field(default=UserRoleEnum.FARMER, example="farmer")
    upi_id: Optional[str] = Field(None, example="farmer@paytm", max_length=50)
    bank_account: Optional[str] = Field(None, example="1234567890123456", max_length=20)
    ifsc_code: Optional[str] = Field(None, example="HDFC0001234", max_length=11)
    
    # Optional profile image
    avatar_id: Optional[UUID] = Field(None, example="123e4567-e89b-12d3-a456-426614174000", description="UUID of uploaded profile image file")

    @validator("first_name", "last_name")
    def validate_name(cls, v):
        if len(v.split(" ")) > 1:
            raise ValueError("No spacing allowed")
        return v

    @validator("terms_agreement")
    def validate_terms_agreement(cls, v):
        if not v:
            raise ValueError("You must agree to terms and conditions")
        return v
    
    @validator("ifsc_code")
    def validate_ifsc_code(cls, v):
        if v and len(v) != 11:
            raise ValueError("IFSC code must be exactly 11 characters")
        return v
    
    @validator("bank_account")
    def validate_bank_account(cls, v):
        if v and not v.isdigit():
            raise ValueError("Bank account number must contain only digits")
        return v

    class Config:
        error_msg_templates = {
            "value_error.any_str.max_length": "50 characters max!",
            "value_error.any_str.min_length": "8 characters min!",
        }


class VerifyOtpSchema(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")
    otp: int


class RequestOtpSchema(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")


class SetNewPasswordSchema(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")
    otp: int
    password: str = Field(..., example="newstrongpassword", min_length=8)

    class Config:
        error_msg_templates = {
            "value_error.any_str.min_length": "8 characters min!",
        }


class LoginUserSchema(BaseModel):
    email: EmailStr = Field(..., example="johndoe@example.com")
    password: str = Field(..., example="password")


class RefreshTokensSchema(BaseModel):
    refresh: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    )


class RegisterResponseSchema(ResponseSchema):
    data: RequestOtpSchema


class TokensResponseDataSchema(BaseModel):
    access: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    )
    refresh: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
    )


class TokensResponseSchema(ResponseSchema):
    data: TokensResponseDataSchema


class KYCVerificationSchema(BaseModel):
    user_id: str = Field(..., example="123e4567-e89b-12d3-a456-426614174000")
    is_verified: bool = Field(..., example=True)


class KYCResponseSchema(ResponseSchema):
    data: dict = Field(default={"message": "KYC verification updated successfully"})
