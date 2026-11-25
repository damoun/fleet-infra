"""Pure builders: ISO-week usage, Immich search requests, ffmpeg and Typst commands."""

from dataclasses import dataclass
from datetime import date, timedelta

REEL_W, REEL_H, FPS = 1080, 1920, 30
SLIDE_W, SLIDE_H = 1080, 1350
HDR_TRANSFERS = {"arib-std-b67", "smpte2084"}
TONEMAP = (
    "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
    "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
)
USED = "used/"
FFMPEG = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-nostats", "-y"]


def iso_week(day: date) -> str:
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def recent_weeks(today: date, n: int) -> list[str]:
    """The current ISO week and the n-1 before it."""
    return [iso_week(today - timedelta(weeks=i)) for i in range(n)]


def download_request(asset_id: str, asset_type: str) -> tuple[str, dict]:
    """Photos come as Immich's oriented preview JPEG/WebP (up to 1440px): the original may be
    HEIC, which ffmpeg 5.1 cannot decode, and fullsize falls back to preview or to the
    unrotated original. Videos use the original."""
    if asset_type == "IMAGE":
        return f"/assets/{asset_id}/thumbnail", {"size": "preview"}
    return f"/assets/{asset_id}/original", {}


def _day(value: str, end: bool = False) -> str:
    """Immich wants date-times; accept plain dates."""
    if len(value) == 10:
        return value + ("T23:59:59.999Z" if end else "T00:00:00.000Z")
    return value


def search_request(
    query: str | None,
    after: str | None,
    before: str | None,
    place: str | None,
    kind: str | None,
    tag_ids: list[str],
    exclude_tag_ids: list[str],
    limit: int,
) -> tuple[str, dict]:
    flt: dict = {}
    if after:
        flt.setdefault("takenAt", {})["gte"] = _day(after)
    if before:
        flt.setdefault("takenAt", {})["lte"] = _day(before, end=True)
    if place:
        flt["or"] = [{"city": {"eq": place}}, {"country": {"eq": place}}]
    if kind:
        flt["type"] = {"eq": kind.upper()}
    if tag_ids:
        flt.setdefault("tagIds", {})["all"] = tag_ids
    if exclude_tag_ids:
        flt.setdefault("tagIds", {})["none"] = exclude_tag_ids
    body: dict = {"filter": flt, "size": limit, "withExif": True}
    if query:
        body["query"] = query
        return "/search/smart", body
    return "/search/metadata", body


def compact_asset(item: dict) -> dict:
    exif = item.get("exifInfo") or {}
    values = [t["value"] for t in item.get("tags") or []]
    used = sorted(v.removeprefix(USED) for v in values if v.startswith(USED))
    duration = item.get("duration")
    return {
        "id": item["id"],
        "type": item["type"].lower(),
        "taken_at": item["fileCreatedAt"],
        "place": ", ".join(p for p in (exif.get("city"), exif.get("country")) if p),
        "duration": duration / 1000 if duration else None,
        "tags": [v for v in values if not v.startswith(USED)],
        "description": exif.get("description") or "",
        "last_used": used[-1] if used else None,
        "use_count": len(used),
    }


@dataclass(frozen=True)
class Probe:
    duration: float
    hdr: bool
    has_audio: bool


def probe_argv(path: str) -> list[str]:
    return [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=codec_type,color_transfer:format=duration",
        "-of", "json", path,
    ]  # fmt: skip


def parse_probe(data: dict) -> Probe:
    streams = data["streams"]
    video = next(s for s in streams if s["codec_type"] == "video")
    return Probe(
        duration=float(data["format"]["duration"]),
        hdr=video.get("color_transfer") in HDR_TRANSFERS,
        has_audio=any(s["codec_type"] == "audio" for s in streams),
    )


def reel_argv(
    segments: list[tuple[str, float, float, Probe]], keep_audio: bool, out: str
) -> list[str]:
    """One ffmpeg run: trim each (path, start, end, probe), normalize, concat, encode."""
    inputs: list[str] = []
    chains: list[str] = []
    joined = ""
    for i, (path, start, end, probe) in enumerate(segments):
        if start >= probe.duration:
            raise ValueError(f"segment {i} starts after the clip ends ({probe.duration:.1f}s)")
        length = min(end, probe.duration) - start
        inputs += ["-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", path]
        color = TONEMAP if probe.hdr else "format=yuv420p"
        video = (
            f"[{i}:v:0]setpts=PTS-STARTPTS,fps={FPS},"
            f"scale={REEL_W}:{REEL_H}:force_original_aspect_ratio=increase,"
            f"crop={REEL_W}:{REEL_H},setsar=1,{color}[v{i}]"
        )
        if keep_audio and probe.has_audio:
            audio = (
                f"[{i}:a:0]aresample=48000,aformat=channel_layouts=stereo,"
                f"atrim=duration={length:.3f},asetpts=PTS-STARTPTS[a{i}]"
            )
        else:
            audio = (
                f"anullsrc=r=48000:cl=stereo,atrim=duration={length:.3f},asetpts=PTS-STARTPTS[a{i}]"
            )
        chains += [video, audio]
        joined += f"[v{i}][a{i}]"
    graph = ";".join(
        [
            *chains,
            f"{joined}concat=n={len(segments)}:v=1:a=1[v][ac]",
            "[ac]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]",
        ]
    )
    return [
        *FFMPEG, *inputs,
        "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "18",
        "-r", str(FPS), "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", out,
    ]  # fmt: skip


def still_argv(src: str, out: str, t: float = 0, hdr: bool = False) -> list[str]:
    """Center-cropped slide-size JPEG from a photo, or from a video at t seconds."""
    vf = (
        f"scale={SLIDE_W}:{SLIDE_H}:force_original_aspect_ratio=increase,"
        f"crop={SLIDE_W}:{SLIDE_H},setsar=1"
    )
    if hdr:
        vf += f",{TONEMAP},format=yuvj420p"
    return [
        *FFMPEG, "-ss", f"{t:.3f}", "-i", src,
        "-vf", vf,
        "-frames:v", "1", "-q:v", "2", out,
    ]  # fmt: skip


def typst_source(markup: str, has_background: bool) -> str:
    bg = (
        ', background: image("bg.jpg", width: 100%, height: 100%, fit: "cover")'
        if has_background
        else ""
    )
    return (
        f"#set page(width: {SLIDE_W}pt, height: {SLIDE_H}pt, margin: 80pt{bg})\n"
        '#set text(font: "Inter", size: 56pt)\n'
        f"{markup}\n"
    )


def typst_argv(root: str, src: str, out: str) -> list[str]:
    # 72 ppi makes one pt one pixel. --root keeps the markup inside the slide directory.
    return ["typst", "compile", "--root", root, "--format", "png", "--ppi", "72", src, out]
