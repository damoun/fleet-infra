"""MCP server: find Immich assets and render Instagram reels and carousels from them."""

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
        "image with a vision tool before choosing segments. "
        "create_* return a job id; poll job_status."
    ),
    host="0.0.0.0",
    port=8000,
    stateless_http=True,
)


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


@mcp.tool()
async def find_assets(
    query: str | None = None,
    after: str | None = None,
    before: str | None = None,
    place: str | None = None,
    tags: list[str] | None = None,
    type: Literal["video", "image"] | None = None,
    not_used_within_weeks: int | None = None,
    limit: int = 30,
) -> list[dict]:
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
        return []
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
    return [plan.compact_asset(i) for i in items]


@mcp.tool()
async def tag_assets(ids: list[AssetId], tags: list[str]) -> str:
    """Upsert tags (full paths such as trip/ibiza) and assign them to the assets."""
    await immich.tag(ids, tags)
    return "ok"


# The return annotation must stay a bare list: a typed list makes FastMCP build an output
# schema that rejects Image.
@mcp.tool()
async def preview_assets(ids: Annotated[list[AssetId], Field(min_length=1, max_length=8)]) -> list:
    """See assets: one contact sheet JPEG and a legend, in a single call.

    Each asset is a row half: three 256px tiles, labelled #k on the first. Videos show frames at
    15%, 50% and 85% of their duration (the legend gives the times, so you can pick segment
    start and end); photos show the photo and two black tiles.
    """
    with tempfile.TemporaryDirectory(dir=work_dir, ignore_cleanup_errors=True) as work:
        legend, jpeg = await pipeline.preview(immich, ids, Path(work))
    return [legend, Image(data=jpeg, format="jpeg")]


@mcp.tool()
async def create_reel(spec: ReelSpec) -> str:
    """Render a 1080x1920 30 fps reel from trimmed segments and upload it to the album.

    Returns a job id. The sources are tagged used/<week> once the reel is uploaded.
    """
    return jobs.submit(lambda work: pipeline.reel(immich, spec, work))


@mcp.tool()
async def create_carousel(spec: CarouselSpec) -> str:
    """Render 1 to 10 1080x1350 slides and upload them to the album in order.

    A slide is a photo (or a video still at t), or Typst markup with an optional
    background asset, available to the markup as image("bg.jpg"). The page is
    1080pt x 1350pt, the font is Inter. Returns a job id.
    """
    return jobs.submit(lambda work: pipeline.carousel(immich, spec, work))


@mcp.tool()
async def job_status(job_id: str) -> dict:
    """Status of a create_* job: queued, running, done (asset_ids) or failed (error)."""
    return jobs.status(job_id)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
