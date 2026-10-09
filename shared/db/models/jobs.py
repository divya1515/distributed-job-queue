from enum import Enum
from uuid import uuid4
import uuid
from datetime import datetime, timezone
from pydantic import EmailStr
from sqlalchemy import BigInteger
from typing import List, TYPE_CHECKING, Optional,Dict,Any
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, ForeignKey, Text, Integer, DateTime, Enum as SQLEnum,JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import Mapped
from shared.db.snowflake import generate_id
from shared.db.database import Base

class JobType(str, Enum):
    bulk_url_shortening="bulk_url_shortening"

class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    partial_failure = "partial_failure"
    completed = "completed"
    failed = "failed"


class Job(Base):
    __tablename__ = "job"
    id: Mapped[int] = mapped_column(BigInteger,primary_key=True,default=generate_id)
    type: Mapped[JobType] = mapped_column(SQLEnum(JobType))
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid4)
    email: Mapped[str] = mapped_column(String(255),nullable=False)
    payload:Mapped[Dict[str,Any]]=mapped_column(JSONB)
    result: Mapped[Optional[Dict[str,Any]]]= mapped_column(JSONB, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[JobStatus] = mapped_column(SQLEnum(JobStatus), default=JobStatus.pending,index=True)
    total_items: Mapped[int] = mapped_column(Integer,default=0)
    completed_items: Mapped[int] = mapped_column(Integer,default=0)
    failed_items: Mapped[int] = mapped_column(Integer,default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),)