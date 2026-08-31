import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.evidence import Evidence


class ControlFramework(str, enum.Enum):
    ISO_27001_2022 = "ISO 27001:2022"
    SOC_2 = "SOC 2"


class ControlStatus(str, enum.Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    IMPLEMENTED = "Implemented"
    EVIDENCED = "Evidenced"


class Control(Base):
    __tablename__ = "controls"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    framework: Mapped[ControlFramework] = mapped_column(Enum(ControlFramework))
    theme: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[ControlStatus] = mapped_column(
        Enum(ControlStatus), default=ControlStatus.NOT_STARTED
    )
    owner_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_reviewed: Mapped[date | None] = mapped_column(Date, nullable=True)

    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="control", cascade="all, delete-orphan"
    )

    @property
    def has_stale_evidence(self) -> bool:
        return any(item.is_stale for item in self.evidence)
