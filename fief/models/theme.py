from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel


class Theme(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "themes"

    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    primary_color: Mapped[str] = mapped_column(String(length=255), nullable=False)
    primary_color_hover: Mapped[str] = mapped_column(String(length=255), nullable=False)
    primary_color_light: Mapped[str] = mapped_column(String(length=255), nullable=False)

    input_color: Mapped[str] = mapped_column(String(length=255), nullable=False)
    input_color_background: Mapped[str] = mapped_column(
        String(length=255), nullable=False
    )

    light_color: Mapped[str] = mapped_column(String(length=255), nullable=False)
    light_color_hover: Mapped[str] = mapped_column(String(length=255), nullable=False)

    text_color: Mapped[str] = mapped_column(String(length=255), nullable=False)
    accent_color: Mapped[str] = mapped_column(String(length=255), nullable=False)

    background_color: Mapped[str] = mapped_column(String(length=255), nullable=False)

    font_size: Mapped[int] = mapped_column(Integer, nullable=False)
    font_family: Mapped[str] = mapped_column(String(length=255), nullable=False)
    font_css_url: Mapped[str | None] = mapped_column(
        String(length=512), default=None, nullable=True
    )

    @classmethod
    def build_default(cls) -> "Theme":
        return cls(
            name="Default",
            default=True,
            primary_color="#f43f5e",
            primary_color_hover="#e11d48",
            primary_color_light="#fda4af",
            input_color="#1e293b",
            input_color_background="#ffffff",
            light_color="#e2e8f0",
            light_color_hover="#cbd5e1",
            text_color="#475569",
            accent_color="#1e293b",
            background_color="#ffffff",
            font_size=16,
            font_family="'Inter', sans-serif",
        )
