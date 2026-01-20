from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Float,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    discord_id = Column(String(50), unique=True, nullable=True, index=True)
    discord_username = Column(String(100), nullable=True)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    manual_rpm = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    api_keys = relationship("ApiKey", back_populates="owner", cascade="all, delete-orphan")
    request_logs = relationship("RequestLog", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    key_encrypted = Column(Text, nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(20), default="pending", index=True)
    tier = Column(Integer, nullable=True)
    is_enabled = Column(Boolean, default=True)
    total_requests = Column(Integer, default=0)
    success_requests = Column(Integer, default=0)
    fail_requests = Column(Integer, default=0)
    fail_streak = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    cooldown_until = Column(DateTime, nullable=True, index=True)
    last_checked_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="api_keys")


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True, index=True)
    action = Column(String(50), default="generate-image")
    ip_address = Column(String(64), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    steps = Column(Integer, nullable=True)
    samples = Column(Integer, nullable=True)
    status = Column(String(20), default="success")
    status_code = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    reject_reason = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="request_logs")


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClientAPIKey(Base):
    """Client-facing API key for calling the relay."""

    __tablename__ = "client_api_keys"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), default="default")
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    prefix = Column(String(16), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    owner = relationship("User")


class AuthAttempt(Base):
    __tablename__ = "auth_attempts"

    id = Column(Integer, primary_key=True)
    ip_address = Column(String(64), nullable=True, index=True)
    username = Column(String(50), nullable=True, index=True)
    action = Column(String(20), nullable=False, index=True)  # login | register
    success = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
