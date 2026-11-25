"""Tool input schemas."""

import re
from typing import Annotated, Self

from pydantic import BaseModel, Field, StringConstraints, model_validator

UUID = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
AssetId = Annotated[str, StringConstraints(pattern=UUID, to_lower=True)]
Week = Annotated[str, StringConstraints(pattern=r"^\d{4}-W(0[1-9]|[1-4]\d|5[0-3])$")]


BRAND_CALL = re.compile(r"#(cover|point|data|cta)\(")
BRAND_EXAMPLE = '#point(handle: "@account", n: 2, of: 6, bg: bg, num: "01", title: "...", body: "...")'


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
    typst: str | None = Field(None, description="Typst markup on a 1080x1350pt page, with the brand kit imported")
    background: AssetId | None = Field(
        None, description="Typst only: asset exposed to the markup as the variable bg"
    )

    @model_validator(mode="after")
    def _one_kind(self) -> Self:
        if (self.photo is None) == (self.typst is None):
            raise ValueError("set exactly one of photo or typst")
        if self.typst is not None:
            if not BRAND_CALL.search(self.typst):
                raise ValueError(f"Typst slides use the brand kit (#cover, #point, #data or #cta), for example {BRAND_EXAMPLE}")
            if self.background and "bg" not in self.typst:
                raise ValueError("slide has a background but its markup never uses it: pass bg: bg to the brand function")
        return self


class CarouselSpec(BaseModel):
    album: str
    caption: str = Field(description="Stored on the first slide only")
    week: Week
    slides: list[Slide] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def _distinct_images(self) -> Self:
        images = [a for s in self.slides for a in (s.photo, s.background) if a]
        if repeated := sorted({a for a in images if images.count(a) > 1}):
            raise ValueError(f"each image goes on one slide only; repeated: {', '.join(repeated)}")
        return self
