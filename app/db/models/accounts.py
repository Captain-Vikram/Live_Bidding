from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped
import enum

from .base import BaseModel, File
from datetime import datetime
from app.core.config import settings

from uuid import UUID as GUUID  # General UUID


class UserRole(enum.Enum):
    FARMER = "FARMER"
    TRADER = "TRADER"
    ADMIN = "ADMIN"


class User(BaseModel):
    __tablename__ = "users"
    first_name: Mapped[str] = Column(String(50))
    last_name: Mapped[str] = Column(String(50))

    email: Mapped[str] = Column(String(), unique=True)
    phone_number: Mapped[str] = Column(String(20), nullable=True, index=True)

    password: Mapped[str] = Column(String())
    is_email_verified: Mapped[bool] = Column(Boolean(), default=False)
    is_superuser: Mapped[bool] = Column(Boolean(), default=False)
    is_staff: Mapped[bool] = Column(Boolean(), default=False)
    terms_agreement: Mapped[bool] = Column(Boolean(), default=False)

    # New fields for agricultural platform
    role: Mapped[UserRole] = Column(Enum(UserRole), default=UserRole.FARMER)
    upi_id: Mapped[str] = Column(String(50), nullable=True)
    bank_account: Mapped[str] = Column(String(20), nullable=True)
    ifsc_code: Mapped[str] = Column(String(11), nullable=True)
    is_verified: Mapped[bool] = Column(Boolean(), default=False)

    avatar_id: Mapped[GUUID] = Column(
        UUID(),
        ForeignKey("files.id", ondelete="CASCADE"),
        unique=True,
    )
    avatar: Mapped[File] = relationship("File", lazy="joined")
    
    # Phase 6: Mobile and notification relationships
    devices = relationship("DeviceRegistration", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notification_logs = relationship("NotificationLog", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")
    locations = relationship("UserLocation", back_populates="user", cascade="all, delete-orphan")
    
    # Phase 5: Price tracking and alert relationships
    alert_subscriptions = relationship("AlertSubscription", back_populates="user", cascade="all, delete-orphan")
    onsite_notifications = relationship("OnSiteNotification", back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return self.full_name


class Jwt(BaseModel):
    __tablename__ = "jwts"
    user_id: Mapped[GUUID] = Column(
        UUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    user: Mapped[User] = relationship("User", lazy="joined")
    access: Mapped[str] = Column(String())
    refresh: Mapped[str] = Column(String())

    def __repr__(self):
        return f"Access - {self.access} | Refresh - {self.refresh}"


class Otp(BaseModel):
    __tablename__ = "otps"
    user_id: Mapped[GUUID] = Column(
        UUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    user: Mapped[User] = relationship("User", lazy="joined")
    code: Mapped[int] = Column(Integer())

    def __repr__(self):
        return f"User - {self.user.full_name} | Code - {self.code}"

    def check_expiration(self):
        now = datetime.utcnow()
        diff = now - self.updated_at
        if diff.total_seconds() > settings.EMAIL_OTP_EXPIRE_SECONDS:
            return True
        return False
