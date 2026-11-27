"""MCP server: find Immich assets and render Instagram reels and carousels from them."""

import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from mcp.server.fastmcp import FastMCP, Image
from pydantic import Field
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from . import pipeline, plan
from .immich import Immich
from .jobs import Jobs
from .models import AssetId, CarouselSpec, ReelSpec

immich = Immich(os.environ["IMMICH_URL"], os.environ["IMMICH_API_KEY"])
work_dir = Path(os.environ["WORK_DIR"])
jobs = Jobs(work_dir)

mcp = FastMCP(
    "studio",
    instructions=(
        "Find clips and photos in Immich, then render a reel or carousel into an Immich album. "
        "preview_assets returns a contact sheet image plus a legend with the frame times: view the "
        "image with a vision tool to shortlist clips, then inspect_clip each one and pick start "
        "and end from its frames and table. "
        "create_* return a job id; poll job_status."
    ),
    host="0.0.0.0",
    port=8000,
    stateless_http=True,
)


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


@mcp.tool(structured_output=False)
async def find_assets(
    query: str | None = None,
    after: str | None = None,
    before: str | None = None,
    place: str | None = None,
    tags: list[str] | None = None,
    type: Literal["video", "image"] | None = None,
    not_used_within_weeks: int | None = None,
    limit: int = 30,
) -> str:
    """Search Immich assets.

    query runs a smart (semantic) search; without it the search is metadata only.
    after/before are dates or date-times. place is an exact city or country name.
    tags are full tag paths, all required. Usage is tracked by used/<ISO week> tags:
    not_used_within_weeks=N skips assets used in the current week or the N-1 before it.
    limit is clamped to 1..1000. Clips are never retired; use_count is the number of used/ tags.
    orientation is portrait, landscape or square (after EXIF rotation), None when unknown.
    """
    by_value = {t["value"]: t["id"] for t in await immich.tags()}
    tag_ids = [by_value.get(t) for t in tags or []]
    if None in tag_ids:
        return "[]"
    recent = plan.recent_weeks(date.today(), not_used_within_weeks or 0)
    path, body = plan.search_request(
        query,
        after,
        before,
        place,
        type,
        tag_ids,
        [by_value[v] for w in recent if (v := f"{plan.USED}{w}") in by_value],
        max(1, min(limit, 1000)),
    )
    items = await immich.search(path, body)
    # Search results may omit tags; the asset endpoint always has them.
    items = [i if "tags" in i else await immich.asset(i["id"]) for i in items]
    # One compact JSON text block; a list return would be one indented block per asset.
    return json.dumps([plan.compact_asset(i) for i in items], ensure_ascii=False)


@mcp.tool(structured_output=False)
async def tag_assets(ids: list[AssetId], tags: list[str]) -> str:
    """Upsert tags (full paths such as trip/ibiza) and assign them to the assets."""
    await immich.tag(ids, tags)
    return "ok"


@mcp.tool(structured_output=False)
async def preview_assets(ids: Annotated[list[AssetId], Field(min_length=1, max_length=8)]) -> list:
    """See assets: one contact sheet JPEG and a legend, in a single call.

    Each asset is a row half: three 256px tiles, labelled #k on the first. Videos show frames at
    15%, 50% and 85% of their duration (the legend gives the times); photos show the photo
    and two black tiles. Use inspect_clip to choose segment start and end.
    """
    with tempfile.TemporaryDirectory(dir=work_dir, ignore_cleanup_errors=True) as work:
        legend, jpeg = await pipeline.preview(immich, ids, Path(work))
    return [legend, Image(data=jpeg, format="jpeg")]


@mcp.tool(structured_output=False)
async def inspect_clip(
    id: AssetId, start: Annotated[float, Field(ge=0)] = 0, end: float | None = None
) -> list:
    """See one video second by second, to choose segment start and end, or to check a reel.

    Returns a text table and a JPEG sheet of frames labelled with their time in the clip: one
    every 0.5s up to 30s of range, at most 60 frames for longer ranges. start/end (seconds)
    narrow the range. Table row per second: loud is the loudest momentary loudness in LUFS
    (silent below -70; screams and music peak near -10), bright is mean luma in percent, motion
    is the mean luma change between frames (near 0 is a still shot, above 5 is fast movement).
    camera is how far the frame moves per frame, in percent of its height (0 on a tripod, 1-3
    on a ride POV, above 5 a whip pan). shake is the jitter around that move (under 0.3
    steady, 0.4-1.3 ride vibration or mild handheld wobble, above 1.5 shaky). blur is
    blurdetect's score (4-6 sharp, 8 and up blurred by motion or darkness). Motion with a low
    camera is action in the scene; motion with a high camera is the phone moving.
    """
    with tempfile.TemporaryDirectory(dir=work_dir, ignore_cleanup_errors=True) as work:
        table, jpeg = await pipeline.inspect(immich, id, start, end, Path(work))
    return [table, Image(data=jpeg, format="jpeg")]


@mcp.tool(structured_output=False)
async def create_reel(spec: ReelSpec) -> str:
    """Render a 1080x1920 30 fps reel from trimmed segments and upload it to the album.

    Returns a job id. The sources are tagged used/<week> once the reel is uploaded.
    """
    return jobs.submit(lambda work: pipeline.reel(immich, spec, work))


@mcp.tool(structured_output=False)
async def create_carousel(spec: CarouselSpec) -> str:
    """Render 1 to 10 1080x1350 slides and upload them to the album in order.

    A slide is a photo (or a video still at t), or Typst markup with an optional
    background asset. Typst markup must start with one brand call: #cover, #point, #data or
    #cta (each takes handle, of and bg; point, data and cta also take n). Pass bg: bg when the
    slide has a background asset. Each image goes on one slide only. Returns a job id.
    """
    return jobs.submit(lambda work: pipeline.carousel(immich, spec, work))


@mcp.tool(structured_output=False)
async def job_status(job_id: str) -> dict:
    """Status of a create_* job: queued, running, done (asset_ids) or failed (error)."""
    return jobs.status(job_id)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
