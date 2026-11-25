"""Tool input schemas."""

import re
from typing import Annotated, Self

from pydantic import BaseModel, Field, StringConstraints, model_validator

UUID = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
AssetId = Annotated[str, StringConstraints(pattern=UUID, to_lower=True)]
Week = Annotated[str, StringConstraints(pattern=r"^\d{4}-W(0[1-9]|[1-4]\d|5[0-3])$")]


# A Typst slide is one brand call (more markup may follow); the background is passed as bg: bg.
BRAND_CALL = re.compile(r"\s*#(cover|point|data|cta)\(")
BG_ARG = re.compile(r"\bbg\s*:\s*bg\b")


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
    typst: str | None = Field(
        None, description="Typst markup starting with #cover, #point, #data or #cta (the brand kit)"
    )
    background: AssetId | None = Field(
        None, description="Typst only: asset exposed to the markup as the variable bg"
    )

    @model_validator(mode="after")
    def _one_kind(self) -> Self:
        if (self.photo is None) == (self.typst is None):
            raise ValueError("set exactly one of photo or typst")
        if self.typst is not None:
            if not BRAND_CALL.match(self.typst):
                raise ValueError(
                    "raw Typst is not accepted: start the slide with one brand call, "
                    "#cover(handle, of, bg, kick, title, sub), #point(handle, n, of, bg, num, title, body), "
                    "#data(handle, n, of, bg, title, rows) or #cta(handle, n, of, bg, title, ask), "
                    'for example #point(handle: "@account", n: 2, of: 6, bg: bg, num: "01", title: "...", body: "...")'
                )
            if bool(self.background) != bool(BG_ARG.search(self.typst)):
                raise ValueError(
                    "pass bg: bg to the brand call exactly when the slide has a background asset"
                )
        return self


class CarouselSpec(BaseModel):
    album: str
    caption: str = Field(description="Stored on the first slide only")
    week: Week
    slides: list[Slide] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def _distinct_images(self) -> Self:
        # Two stills from one video at different times are two images.
        images = [(s.photo, s.t) if s.photo else (s.background, 0) for s in self.slides]
        images = [i for i in images if i[0]]
        if repeated := sorted({a for a, t in images if images.count((a, t)) > 1}):
            raise ValueError(
                f"each image goes on one slide only; repeated: {', '.join(repeated)}. "
                "Pick a different asset for one of the slides, or drop the background"
            )
        return self
