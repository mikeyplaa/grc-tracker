import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.evidence import Evidence


class ControlTheme(str, enum.Enum):
    ORGANIZATIONAL = "Organizational"
    PEOPLE = "People"
    PHYSICAL = "Physical"
    TECHNOLOGICAL = "Technological"


class ControlStatus(str, enum.Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    IMPLEMENTED = "Implemented"
    EVIDENCED = "Evidenced"


class Control(Base):
    __tablename__ = "controls"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    theme: Mapped[ControlTheme] = mapped_column(Enum(ControlTheme))
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
