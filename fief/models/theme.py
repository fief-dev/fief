from sqlalchemy import Boolean, Column, Integer, String

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel


class Theme(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "themes"

    name: str = Column(String(length=255), nullable=False)
    default: bool = Column(Boolean, default=False, nullable=False)

    primary_color: str = Column(String(length=255), nullable=False)
    primary_color_hover: str = Column(String(length=255), nullable=False)
    primary_color_light: str = Column(String(length=255), nullable=False)

    input_color: str = Column(String(length=255), nullable=False)
    input_color_background: str = Column(String(length=255), nullable=False)

    light_color: str = Column(String(length=255), nullable=False)
    light_color_hover: str = Column(String(length=255), nullable=False)

    text_color: str = Column(String(length=255), nullable=False)
    accent_color: str = Column(String(length=255), nullable=False)

    background_color: str = Column(String(length=255), nullable=False)

    font_size: int = Column(Integer, nullable=False)
    font_family: str = Column(String(length=255), nullable=False)
    font_css_url: str | None = Column(String(length=512), default=None, nullable=True)

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
