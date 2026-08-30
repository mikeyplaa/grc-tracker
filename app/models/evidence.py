from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base

if TYPE_CHECKING:
    from app.models.control import Control


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    control_id: Mapped[str] = mapped_column(ForeignKey("controls.id"))
    title: Mapped[str] = mapped_column(String)
    file_path_or_url: Mapped[str] = mapped_column(String)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    review_due: Mapped[date | None] = mapped_column(Date, nullable=True)

    control: Mapped["Control"] = relationship(back_populates="evidence")
