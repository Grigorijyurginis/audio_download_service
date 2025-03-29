import datetime
import uuid
from typing import Annotated

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from database import Base

str_50 = Annotated[str, 50]
pk = Annotated[int, mapped_column(primary_key=True)]
uuid_type = Annotated[uuid.UUID, mapped_column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
updated_at = Annotated[datetime.datetime, mapped_column(nullable=True, onupdate=text("TIMEZONE('utc', now())"))]
bool_default_false = Annotated[bool, mapped_column(default=False)]


class User(Base):
    __tablename__ = "users"

    id: Mapped[pk]
    uuid: Mapped[uuid_type]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    email: Mapped[str_50]
    is_superuser: Mapped[bool_default_false]

    audio_files = relationship("AudioFile", back_populates="user")


class AudioFile(Base):
    __tablename__ = "audio_files"

    id: Mapped[pk]
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str_50]
    path: Mapped[str]

    user = relationship("User", back_populates="audio_files")
