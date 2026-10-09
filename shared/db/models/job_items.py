from __future__ import annotations
from enum import Enum
from uuid import uuid4
from typing import List,Optional
from sqlalchemy import String,Text,DateTime,BigInteger,ForeignKey,Index,Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship
from sqlalchemy.orm import Mapped 
from sqlalchemy.orm import relationship
from datetime import timezone,datetime
from shared.db.database import Base
from shared.db.snowflake import generate_id

class JobItemStatus(str,Enum):
    pending = "pending"
    processing = "processing"
    success = "success"
    failed = "failed"
    dead_letter = "dead_letter"

class JobItems(Base):
    __tablename__="job_item"
    id:Mapped[int]=mapped_column(BigInteger,primary_key=True,default=generate_id)
    job_id:Mapped[int]=mapped_column(BigInteger,ForeignKey("job.id"))
    item_index:Mapped[int]=mapped_column(BigInteger)
    original_url: Mapped[str]=mapped_column(Text,nullable=False)
    short_url: Mapped[Optional[str]]=mapped_column(String(255),nullable=True)
    status: Mapped[JobItemStatus]=mapped_column(SQLEnum(JobItemStatus),default=JobItemStatus.pending)
    attempts: Mapped[int]=mapped_column(BigInteger,default=0)
    max_attempts: Mapped[int]=mapped_column(BigInteger,default=3)
    error_message: Mapped[Optional[str]]=mapped_column(Text,nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),
                                               default= lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),
                                               default= lambda: datetime.now(timezone.utc),
                                               onupdate= lambda: datetime.now(timezone.utc))
    __table_args__ = (
        Index("ix_job_item_job_status","job_id","status"),
    )