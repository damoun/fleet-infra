"""Job bodies: download, render with ffmpeg or Typst, upload, album, tag."""

import asyncio
import json
from pathlib import Path

from . import plan
from .immich import Immich
from .models import CarouselSpec, ReelSpec


async def run(argv: list[str], timeout: int = 600) -> bytes:
    proc = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError(f"{argv[0]} timed out after {timeout}s") from None
    if proc.returncode:
        raise RuntimeError(f"{argv[0]} exited {proc.returncode}: {err.decode()[-800:]}")
    return out


async def _download(immich: Immich, asset_ids: list[str], work: Path) -> dict[str, Path]:
    paths = {i: work / i for i in dict.fromkeys(asset_ids)}
    for asset_id, path in paths.items():
        kind = (await immich.asset(asset_id))["type"]
        await immich.download(*plan.download_request(asset_id, kind), path)
    return paths


async def _publish(
    immich: Immich, files: list[Path], album: str, caption: str, sources: list[str], week: str
) -> list[str]:
    """Upload in order, caption on the first, add to the album, mark the sources used."""
    created = [await immich.upload(f, f.name) for f in files]
    await immich.describe(created[0], caption)
    await immich.add_to_album(await immich.album(album), created)
    await immich.tag(list(dict.fromkeys(sources)), [f"{plan.USED}{week}"])
    return created


async def reel(immich: Immich, spec: ReelSpec, work: Path) -> list[str]:
    sources = [s.asset_id for s in spec.segments]
    paths = await _download(immich, sources, work)
    probes = {
        i: plan.parse_probe(json.loads(await run(plan.probe_argv(str(p)), 60)))
        for i, p in paths.items()
    }
    out = work / "reel.mp4"
    segments = [(str(paths[s.asset_id]), s.start, s.end, probes[s.asset_id]) for s in spec.segments]
    await run(plan.reel_argv(segments, spec.keep_audio, str(out)))
    return await _publish(immich, [out], spec.album, spec.caption, sources, spec.week)


async def carousel(immich: Immich, spec: CarouselSpec, work: Path) -> list[str]:
    sources = [a for s in spec.slides for a in (s.photo, s.background) if a]
    paths = await _download(immich, sources, work)
    files: list[Path] = []
    for n, slide in enumerate(spec.slides, 1):
        slide_dir = work / f"slide{n}"
        slide_dir.mkdir()
        if slide.photo:
            out = slide_dir / f"slide{n}.jpg"
            await run(plan.still_argv(str(paths[slide.photo]), str(out), slide.t))
        else:
            if slide.background:
                await run(plan.still_argv(str(paths[slide.background]), str(slide_dir / "bg.jpg")))
            src, out = slide_dir / "slide.typ", slide_dir / f"slide{n}.png"
            src.write_text(plan.typst_source(slide.typst, slide.background is not None))
            await run(plan.typst_argv(str(slide_dir), str(src), str(out)), 60)
        files.append(out)
    return await _publish(immich, files, spec.album, spec.caption, sources, spec.week)
