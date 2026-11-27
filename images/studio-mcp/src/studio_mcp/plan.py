"""Pure builders: ISO-week usage, Immich search requests, ffmpeg and Typst commands."""

import math
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

REEL_W, REEL_H, FPS = 1080, 1920, 30
SLIDE_W, SLIDE_H = 1080, 1350
HDR_TRANSFERS = {"arib-std-b67", "smpte2084"}
TONEMAP = (
    "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
    "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
)
TILE, PER_ROW, FRACTIONS = 256, 2, (0.15, 0.5, 0.85)
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


def orientation(item: dict) -> str | None:
    """From the asset-level width and height, which Immich reports after EXIF rotation."""
    w, h = item.get("width"), item.get("height")
    if not w or not h:
        return None
    if h > w:
        return "portrait"
    if w > h:
        return "landscape"
    return "square"


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
        "orientation": orientation(item),
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


def segment_argv(
    path: str, start: float, end: float, probe: Probe, keep_audio: bool, out: str
) -> list[str]:
    """Trim and normalize one segment into an mkv that stream-copies with its siblings.

    Every segment is a separate run: decoding all sources in one filter graph queues 4K
    frames for the inputs concat is not reading yet, and memory grows with the segment count.
    """
    if start >= probe.duration:
        raise ValueError(f"{path} starts after the clip ends ({probe.duration:.1f}s)")
    # Whole frames: 48000/30 = 1600 samples per frame, so audio and video lengths match exactly.
    frames = round((min(end, probe.duration) - start) * FPS)
    if frames < 1:
        raise ValueError(f"{path}: segment is shorter than one frame")
    length = frames / FPS
    color = TONEMAP if probe.hdr else "format=yuv420p"
    video = (
        f"[0:v:0]setpts=PTS-STARTPTS,fps={FPS},"
        f"scale={REEL_W}:{REEL_H}:force_original_aspect_ratio=increase,"
        f"crop={REEL_W}:{REEL_H},setsar=1,{color}[v]"
    )
    if keep_audio and probe.has_audio:
        source = (
            f"[0:a:0]aresample=48000,aformat=channel_layouts=stereo,apad=whole_dur={length:.6f}"
        )
    else:
        source = "anullsrc=r=48000:cl=stereo"
    audio = f"{source},atrim=duration={length:.6f},asetpts=PTS-STARTPTS[a]"
    return [
        *FFMPEG, "-ss", f"{start:.3f}", "-t", f"{length:.6f}", "-i", path,
        "-filter_complex", f"{video};{audio}", "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p", "-crf", "16",
        "-preset", "veryfast", "-r", str(FPS),
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", out,
    ]  # fmt: skip


def concat_list(names: list[str]) -> str:
    """Entries are relative: the demuxer resolves them against the list file's directory."""
    return "".join(f"file '{n}'\n" for n in names)


def concat_argv(list_path: str, out: str) -> list[str]:
    """Join the segments without re-encoding video; loudness is normalized once over the reel.

    -ar resamples after loudnorm: PCM in mkv has no channel layout, and an explicit aresample
    after loudnorm then fails to negotiate one.
    """
    return [
        *FFMPEG, "-f", "concat", "-i", list_path,
        "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
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


@dataclass(frozen=True)
class Preview:
    asset_id: str
    path: str
    is_video: bool
    duration: float  # seconds, 0 for photos
    orientation: str | None
    error: str | None = None  # the asset could not be loaded: its tiles stay black


def preview_request(asset_id: str, asset_type: str) -> tuple[str, dict]:
    """Like download_request, but videos use the web playback file: smaller than the original."""
    if asset_type == "VIDEO":
        return f"/assets/{asset_id}/video/playback", {}
    return download_request(asset_id, asset_type)


def frame_times(duration: float) -> list[float]:
    """Three times inside the clip, or one frame at 0 when the duration is unknown."""
    if duration <= 0:
        return [0.0]
    return [round(max(0.0, min(duration * f, duration - 0.25)), 3) for f in FRACTIONS]


BLACK = ["-f", "lavfi", "-i", f"color=c=black:s={TILE}x{TILE}"]


def black_argv(out: str) -> list[str]:
    return [*FFMPEG, *BLACK, "-frames:v", "1", out]


def asset_tiles(k: int, asset: Preview, tiles_dir: str) -> list[list[str]]:
    """One ffmpeg argv per tile file of asset #k, three tiles in order.

    Videos get three frames; photos the photo and two black tiles; unavailable assets three
    black tiles. Each tile is a 256px box with the aspect kept and black padding, and the
    asset's first tile carries its #k label.
    """
    fit = (
        f"scale={TILE}:{TILE}:force_original_aspect_ratio=decrease,"
        f"pad={TILE}:{TILE}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
    )
    label = (
        f",drawtext=text='#{k}':font=Inter:fontsize=28:fontcolor=white"
        ":box=1:boxcolor=black@0.6:boxborderw=4:x=6:y=6"
    )
    if asset.error:
        times = []
    elif asset.is_video:
        times = frame_times(asset.duration)
    else:
        times = [0.0]
    frames = [
        ["-ss", f"{t:.3f}", "-i", asset.path, "-vf", fit + (label if j == 0 else "")]
        for j, t in enumerate(times)
    ]
    inputs = frames + [BLACK] * (len(FRACTIONS) - len(frames))
    first = (k - 1) * len(FRACTIONS)
    return [
        [*FFMPEG, *tile, "-frames:v", "1", f"{tiles_dir}/t{first + n:02d}.png"]
        for n, tile in enumerate(inputs, 1)
    ]


def tile_argvs(assets: list[Preview], tiles_dir: str) -> list[list[str]]:
    """The tile argvs of all assets, t01.png, t02.png, ... in order."""
    return [argv for k, a in enumerate(assets, 1) for argv in asset_tiles(k, a, tiles_dir)]


def sheet_argv(tiles_dir: str, assets: int, out: str) -> list[str]:
    """Tile t01.png.. into a sheet PER_ROW assets wide, as many rows as needed."""
    rows = -(-assets // PER_ROW)
    return [
        *FFMPEG, "-framerate", "1", "-i", f"{tiles_dir}/t%02d.png",
        "-vf", f"tile={PER_ROW * len(FRACTIONS)}x{rows}", "-frames:v", "1", "-q:v", "3", out,
    ]  # fmt: skip


def legend(assets: list[Preview]) -> str:
    lines = []
    for k, a in enumerate(assets, 1):
        if a.error:
            lines.append(f"#{k} {a.asset_id} unavailable: {a.error}")
            continue
        line = (
            f"#{k} {a.asset_id} {'video' if a.is_video else 'image'} {a.orientation or 'unknown'}"
        )
        if a.is_video and a.duration <= 0:
            line += " duration unknown"
        elif a.is_video:
            times = "/".join(f"{t:.1f}" for t in frame_times(a.duration))
            line += f" {a.duration:.1f}s frames at {times}s"
        lines.append(line)
    return "\n".join(lines)


INSPECT_FRAMES, INSPECT_HEIGHT, SILENT = 60, 240, -70.0
YAVG, YDIF, LOUD = "lavfi.signalstats.YAVG", "lavfi.signalstats.YDIF", "lavfi.r128.M"


def inspect_rate(span: float) -> int:
    """k for one frame every k/2 seconds: 0.5s up to 30s of clip, then at most INSPECT_FRAMES."""
    return max(1, math.ceil(span * 2 / INSPECT_FRAMES))


def inspect_video_argv(
    path: str, start: float, span: float, portrait: bool, hdr: bool, sheet: str, stats: str
) -> list[str]:
    """One decode: a timestamped frame sheet, and luma stats of every frame into stats.

    Frames are labelled with their time in the clip, not in the inspected range. HDR is
    tonemapped like the reel, so the sheet and the brightness match what gets rendered.
    """
    k = inspect_rate(span)
    cols = 10 if portrait else 5
    frames = math.floor(span * 2 / k) + 1
    rows = math.ceil(frames / cols)
    t = f"t+{start:.3f}"
    label = (
        f"drawtext=font=Inter:text='%{{eif\\:trunc({t})\\:d}}.%{{eif\\:mod(trunc(({t})*10),10)\\:d}}s'"
        ":x=4:y=4:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6"
    )
    graph = (
        f"[0:v:0]scale=-2:{INSPECT_HEIGHT},{TONEMAP if hdr else 'format=yuv420p'},split[s][m];"
        f"[s]fps=2/{k},{label},tile={cols}x{rows}[sheet];"
        f"[m]signalstats,metadata=print:file={stats}[stats]"
    )
    return [
        *FFMPEG, "-ss", f"{start:.3f}", "-t", f"{span:.3f}", "-i", path,
        "-filter_complex", graph,
        "-map", "[sheet]", "-frames:v", "1", "-q:v", "3", sheet,
        "-map", "[stats]", "-f", "null", "-",
    ]  # fmt: skip


def inspect_audio_argv(path: str, start: float, span: float, stats: str) -> list[str]:
    """Momentary loudness (400 ms window) every 100 ms into stats."""
    return [
        *FFMPEG, "-ss", f"{start:.3f}", "-t", f"{span:.3f}", "-i", path, "-vn",
        "-af", f"ebur128=metadata=1,ametadata=print:key={LOUD}:file={stats}",
        "-f", "null", "-",
    ]  # fmt: skip


def parse_metadata(text: str) -> list[tuple[float, dict[str, float]]]:
    """ffmpeg metadata=print output: (pts_time, {key: value}) per frame, lavfi keys only.

    Decoder entries such as timecode=01:02:03:04 are printed too and are not numbers.
    """
    frames: list[tuple[float, dict[str, float]]] = []
    for line in text.splitlines():
        if line.startswith("frame:"):
            frames.append((float(line.rsplit("pts_time:", 1)[1]), {}))
        elif line.startswith("lavfi.") and frames:
            key, value = line.split("=", 1)
            frames[-1][1][key] = float(value)
    return frames


def inspect_table(
    start: float,
    span: float,
    video: list[tuple[float, dict[str, float]]],
    audio: list[tuple[float, dict[str, float]]] | None,
) -> str:
    """One row per second of the range, in clip time: loudest moment, mean brightness, motion."""
    seconds = range(math.ceil(span))

    def bucket(frames, key):
        out: dict[int, list[float]] = {s: [] for s in seconds}
        for t, values in frames:
            if key in values and int(t) in out:
                out[int(t)].append(values[key])
        return out

    bright, motion = bucket(video, YAVG), bucket(video, YDIF)
    loud = bucket(audio, LOUD) if audio is not None else None
    rows = ["t(s) loud(LUFS) bright(%) motion"]
    for s in seconds:
        if not bright[s]:
            continue
        if loud is None:
            level = "no-audio"
        elif not loud[s] or max(loud[s]) < SILENT:
            level = "silent"
        else:
            level = f"{max(loud[s]):.0f}"
        avg = sum(bright[s]) / len(bright[s]) / 255 * 100
        rows.append(f"{start + s:g} {level} {avg:.0f} {sum(motion[s]) / len(motion[s]):.1f}")
    return "\n".join(rows)


BRAND = Path(__file__).with_name("brand.typ")


def typst_source(markup: str, has_background: bool) -> str:
    """The brand kit import, page defaults, and `bg` bound to the background or none."""
    bg = '"bg.jpg"' if has_background else "none"
    return (
        '#import "brand.typ": *\n'
        f"#set page(width: {SLIDE_W}pt, height: {SLIDE_H}pt, margin: 80pt, fill: night)\n"
        '#set text(font: "Inter", size: 56pt, fill: snow)\n'
        f"#let bg = {bg}\n"
        f"{markup}\n"
    )


def typst_argv(root: str, src: str, out: str) -> list[str]:
    # 72 ppi makes one pt one pixel. --root keeps the markup inside the slide directory.
    return ["typst", "compile", "--root", root, "--format", "png", "--ppi", "72", src, out]
