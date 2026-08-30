from datetime import datetime

from sqlalchemy import JSON, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db import Base


class ScoreSnapshot(Base):
    __tablename__ = "score_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    taken_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    overall_score: Mapped[float] = mapped_column(Float)
    theme_scores: Mapped[dict[str, float]] = mapped_column(JSON)
