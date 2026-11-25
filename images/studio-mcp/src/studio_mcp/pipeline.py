"""Job bodies: download, render with ffmpeg or Typst, upload, album, tag."""

import asyncio
import json
from pathlib import Path

from . import plan
from .immich import Immich
from .models import CarouselSpec, ReelSpec

PREVIEW_TIMEOUT, STEP_TIMEOUT = 90, 30


async def run(argv: list[str], timeout: int = 600) -> bytes:
    proc = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout)
    except BaseException as e:  # includes cancellation: never leave ffmpeg running
        proc.kill()
        await proc.wait()
        if isinstance(e, TimeoutError):
            raise RuntimeError(f"{argv[0]} timed out after {timeout}s") from None
        raise
    if proc.returncode:
        raise RuntimeError(f"{argv[0]} exited {proc.returncode}: {err.decode()[-800:]}")
    return out


async def _download(
    immich: Immich, asset_ids: list[str], work: Path
) -> tuple[dict[str, Path], set[str]]:
    """Paths by asset id, and the ids that are videos."""
    paths = {i: work / i for i in asset_ids}
    videos = set()
    for asset_id, path in paths.items():
        kind = (await immich.asset(asset_id))["type"]
        await immich.download(*plan.download_request(asset_id, kind), path)
        if kind == "VIDEO":
            videos.add(asset_id)
    return paths, videos


async def _probe(path: Path) -> plan.Probe:
    return plan.parse_probe(json.loads(await run(plan.probe_argv(str(path)), 60)))


async def _still(path: Path, out: Path, t: float, is_video: bool) -> None:
    hdr = is_video and (await _probe(path)).hdr
    await run(plan.still_argv(str(path), str(out), t, hdr))


async def _publish(
    immich: Immich, files: list[Path], spec: ReelSpec | CarouselSpec, sources: list[str]
) -> list[str]:
    """Upload in order, caption on the first, add to the album, mark the sources used."""
    created = [await immich.upload(f) for f in files]
    await immich.describe(created[0], spec.caption)
    await immich.add_to_album(await immich.album(spec.album), created)
    await immich.tag(sources, [f"{plan.USED}{spec.week}"])
    return created


async def reel(immich: Immich, spec: ReelSpec, work: Path) -> list[str]:
    sources = list(dict.fromkeys(s.asset_id for s in spec.segments))
    paths, _ = await _download(immich, sources, work)
    probes = {i: await _probe(p) for i, p in paths.items()}
    parts = []
    for n, s in enumerate(spec.segments, 1):
        part = str(work / f"seg{n:02d}.mkv")
        argv = plan.segment_argv(
            str(paths[s.asset_id]), s.start, s.end, probes[s.asset_id], spec.keep_audio, part
        )
        await run(argv)
        parts.append(part)
    (work / "list.txt").write_text(plan.concat_list(parts))
    out = work / "reel.mp4"
    await run(plan.concat_argv(str(work / "list.txt"), str(out)))
    return await _publish(immich, [out], spec, sources)


async def carousel(immich: Immich, spec: CarouselSpec, work: Path) -> list[str]:
    sources = list(dict.fromkeys(a for s in spec.slides for a in (s.photo, s.background) if a))
    paths, videos = await _download(immich, sources, work)
    files: list[Path] = []
    for n, slide in enumerate(spec.slides, 1):
        slide_dir = work / f"slide{n}"
        slide_dir.mkdir()
        if slide.photo:
            out = slide_dir / f"slide{n}.jpg"
            await _still(paths[slide.photo], out, slide.t, slide.photo in videos)
        else:
            if slide.background:
                bg = slide.background
                await _still(paths[bg], slide_dir / "bg.jpg", 0, bg in videos)
            src, out = slide_dir / "slide.typ", slide_dir / f"slide{n}.png"
            src.write_text(plan.typst_source(slide.typst, slide.background is not None))
            await run(plan.typst_argv(str(slide_dir), str(src), str(out)), 60)
        files.append(out)
    return await _publish(immich, files, spec, sources)


async def preview(immich: Immich, ids: list[str], work: Path) -> tuple[str, bytes]:
    """A contact sheet JPEG of the assets and the legend that maps tiles back to ids."""
    try:
        async with asyncio.timeout(PREVIEW_TIMEOUT):
            return await _preview(immich, ids, work)
    except TimeoutError:
        raise RuntimeError(f"preview timed out after {PREVIEW_TIMEOUT}s") from None


async def _run_tiles(argvs: list[list[str]]) -> None:
    for argv in argvs:
        await run(argv, STEP_TIMEOUT)
        out = Path(argv[-1])
        # ffmpeg exits 0 without a frame when -ss lands past the last one; keep the slot.
        if not out.exists() or not out.stat().st_size:
            await run(plan.black_argv(argv[-1]), STEP_TIMEOUT)


async def _preview(immich: Immich, ids: list[str], work: Path) -> tuple[str, bytes]:
    tiles = work / "tiles"
    tiles.mkdir()
    assets = []
    for k, asset_id in enumerate(ids, 1):
        try:
            info = await immich.asset(asset_id)
            path = work / asset_id
            await immich.download(*plan.preview_request(asset_id, info["type"]), path)
            asset = plan.Preview(
                asset_id,
                str(path),
                info["type"] == "VIDEO",
                (info.get("duration") or 0) / 1000,
                plan.orientation(info),
            )
            await _run_tiles(plan.asset_tiles(k, asset, str(tiles)))
        except Exception as e:  # e.g. the preview thumbnail of a fresh upload does not exist yet
            reason = " ".join(str(e).split())[:100]
            asset = plan.Preview(asset_id, "", False, 0, None, f"{type(e).__name__}: {reason}")
            await _run_tiles(plan.asset_tiles(k, asset, str(tiles)))
        assets.append(asset)
    sheet = work / "sheet.jpg"
    await run(plan.sheet_argv(str(tiles), len(assets), str(sheet)), STEP_TIMEOUT)
    return plan.legend(assets), sheet.read_bytes()
