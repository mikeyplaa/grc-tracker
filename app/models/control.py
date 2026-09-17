import enum
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, String, Text, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.evidence import Evidence


class ControlFramework(str, enum.Enum):
    ISO_27001_2022 = "ISO 27001:2022"
    SOC_2 = "SOC 2"
    ISO_42001_2023 = "ISO 42001:2023"


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

    # Trust centre publishing. Nothing is visible on the public /trust
    # surface until is_public is explicitly set from the admin UI.
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="control", cascade="all, delete-orphan"
    )

    @property
    def has_stale_evidence(self) -> bool:
        return any(item.is_stale for item in self.evidence)

    @property
    def evidence_last_refreshed(self) -> datetime | None:
        """Most recent evidence upload date, or None if there is no evidence.

        The trust centre publishes this (plus a count) instead of the evidence
        items themselves -- freshness is the trust signal; titles and file
        locations stay private.
        """
        if not self.evidence:
            return None
        return max(item.uploaded_at for item in self.evidence)
