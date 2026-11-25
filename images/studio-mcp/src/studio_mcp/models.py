"""Tool input schemas."""

from typing import Annotated, Self

from pydantic import BaseModel, Field, StringConstraints, model_validator

UUID = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
AssetId = Annotated[str, StringConstraints(pattern=UUID, to_lower=True)]
Week = Annotated[str, StringConstraints(pattern=r"^\d{4}-W(0[1-9]|[1-4]\d|5[0-3])$")]


class Segment(BaseModel):
    asset_id: AssetId
    start: float = Field(ge=0, description="Seconds into the clip")
    end: float = Field(description="Seconds into the clip, after start")

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if self.end <= self.start:
            raise ValueError("end must be after start")
        return self


class ReelSpec(BaseModel):
    album: str = Field(description="Immich album that receives the reel, created if missing")
    caption: str = Field(description="Stored as the asset description")
    week: Week = Field(description="ISO week such as 2026-W48, used for the used/ tag")
    segments: list[Segment] = Field(min_length=1)
    keep_audio: bool = True


class Slide(BaseModel):
    photo: AssetId | None = Field(None, description="Photo, or video still taken at t")
    t: float = Field(0, ge=0, description="Seconds into a video for the still")
    typst: str | None = Field(None, description="Typst markup, rendered on a 1080x1350pt page")
    background: AssetId | None = Field(
        None, description='Typst only: asset exposed to the markup as image("bg.jpg")'
    )

    @model_validator(mode="after")
    def _one_kind(self) -> Self:
        if (self.photo is None) == (self.typst is None):
            raise ValueError("set exactly one of photo or typst")
        return self


class CarouselSpec(BaseModel):
    album: str
    caption: str = Field(description="Stored on the first slide only")
    week: Week
    slides: list[Slide] = Field(min_length=1, max_length=10)
