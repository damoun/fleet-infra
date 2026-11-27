"""Run inside the image: render generated clips and a Typst slide, then check the outputs.

docker run --rm -v $PWD/tests:/t --entrypoint python studio-mcp:test /t/smoke.py
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from studio_mcp import plan

work = Path(tempfile.mkdtemp())


def sh(argv):
    # errors: vidstabtransform logs the end-of-file byte of its motion file.
    return subprocess.run(argv, check=True, capture_output=True, text=True, errors="replace").stdout


def ffprobe(path, entries):
    out = sh(["ffprobe", "-v", "error", "-show_entries", entries, "-of", "json", str(path)])
    return json.loads(out)


gen = ["ffmpeg", "-hide_banner", "-y", "-f", "lavfi", "-i"]
sdr, hdr = work / "sdr.mp4", work / "hdr.mp4"
sh([*gen, "testsrc=size=640x360:rate=25:duration=3", "-f", "lavfi", "-i", "sine=duration=3",
    "-c:v", "libx264", "-c:a", "aac", "-shortest", str(sdr)])  # fmt: skip
sh([*gen, "testsrc2=size=640x360:rate=24:duration=3", "-vf", "format=yuv420p10le",
    "-c:v", "libx264", "-profile:v", "high10", "-colorspace", "bt2020nc",
    "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", str(hdr)])  # fmt: skip

probes = [plan.parse_probe(json.loads(sh(plan.probe_argv(str(p))))) for p in (sdr, hdr)]
assert [p.hdr for p in probes] == [False, True], probes
assert [p.has_audio for p in probes] == [True, False], probes


def render_reel(name, segments, stabilize=False):
    """Two stages like the pipeline. segments: (clip, probe, start, end). Returns (mp4, seconds)."""
    names, expected = [], 0
    for n, (clip, probe, start, end) in enumerate(segments, 1):
        names.append(f"{name}{n}.mkv")
        trf = str(work / f"{name}{n}.trf") if stabilize else None
        if trf:
            sh(plan.stabilize_argv(str(clip), start, end, probe, trf))
        sh(plan.segment_argv(str(clip), start, end, probe, True, str(work / names[-1]), trf))
        expected += round((min(end, probe.duration) - start) * plan.FPS) / plan.FPS
    listing = work / f"{name}.txt"
    listing.write_text(plan.concat_list(names))  # relative names: resolved against the list's dir
    out = work / f"{name}.mp4"
    sh(plan.concat_argv(str(listing), str(out)))
    return out, expected


out, expected = render_reel("reel", [(sdr, probes[0], 0.5, 2.5), (hdr, probes[1], 1, 3)])
v = ffprobe(
    out, "stream=codec_type,codec_name,profile,width,height,pix_fmt,r_frame_rate,sample_rate"
)
print(json.dumps(v["streams"]))
video = next(s for s in v["streams"] if s["codec_type"] == "video")
audio = next(s for s in v["streams"] if s["codec_type"] == "audio")
assert (video["codec_name"], video["profile"]) == ("h264", "High")
assert (video["width"], video["height"]) == (1080, 1920)
assert video["r_frame_rate"] == "30/1" and video["pix_fmt"] == "yuv420p"
assert (audio["codec_name"], audio["sample_rate"]) == ("aac", "48000")
total = float(ffprobe(out, "format=duration")["format"]["duration"])
assert abs(total - expected) <= 1 / plan.FPS, (total, expected)
print(f"reel {total:.3f}s, expected {expected:.3f}s")

# Stabilized HDR segment: vidstab runs after the tonemap, on 8-bit reel frames.
out, expected = render_reel("stab", [(hdr, probes[1], 1, 3)], stabilize=True)
v = ffprobe(out, "stream=codec_type,width,height,pix_fmt:format=duration")
assert abs(float(v["format"]["duration"]) - expected) <= 1 / plan.FPS, v
assert (v["streams"][0]["width"], v["streams"][0]["pix_fmt"]) == (1080, "yuv420p"), v
print(f"stabilized reel {expected:.3f}s")

# A/V sync: a clip whose audio (2.5s) is shorter than its video (3s) must not shift the reel.
skew = work / "skew.mp4"
sh([*gen, "testsrc=size=640x360:rate=25:duration=3", "-f", "lavfi", "-i", "sine=duration=2.5",
    "-c:v", "libx264", "-c:a", "aac", str(skew)])  # fmt: skip
skew_probe = plan.parse_probe(json.loads(sh(plan.probe_argv(str(skew)))))
out, expected = render_reel("sync", [(skew, skew_probe, 0, 3), (sdr, probes[0], 0.5, 2.5)])
streams = ffprobe(out, "stream=codec_type,duration")["streams"]
d = {s["codec_type"]: float(s["duration"]) for s in streams}
total = float(ffprobe(out, "format=duration")["format"]["duration"])
print(
    f"sync: video {d['video']:.3f}s audio {d['audio']:.3f}s total {total:.3f}s expected {expected:.3f}s"
)
assert abs(d["audio"] - d["video"]) <= 1 / plan.FPS, d
assert abs(total - expected) <= 1 / plan.FPS, (total, expected)

bg = work / "bg.jpg"
sh(plan.still_argv(str(sdr), str(bg), 1))
size = ffprobe(bg, "stream=width,height")["streams"][0]
assert (size["width"], size["height"]) == (1080, 1350)
hdr_still = work / "hdr.jpg"
sh(plan.still_argv(str(hdr), str(hdr_still), 1, hdr=True))
size = ffprobe(hdr_still, "stream=width,height,pix_fmt")["streams"][0]
assert (size["width"], size["height"]) == (1080, 1350), size
# Typst slides: free-form markup and a brand cover over the background, in a slide dir as the
# pipeline lays it out (brand.typ and bg.jpg next to the source).
assert "Lilita One" in sh(["typst", "fonts"]), "brand font missing"
slide = work / "slide1"
slide.mkdir()
shutil.copy(plan.BRAND, slide / "brand.typ")
shutil.copy(bg, slide / "bg.jpg")
rows = '(("Lundi", "low", "Calme"), ("Samedi", "peak", "Très chargé"))'
for name, markup, has_bg in (
    ("free", "#align(center + horizon)[= Hello]", False),
    ("cover", '#cover(handle: "@t", of: 4, bg: bg, kick: "Efteling", title: "Hi", sub: "s")', True),
    ("cover-bare", '#cover(title: "Hi")', False),
    ("point", '#point(handle: "@t", n: 2, of: 4, bg: bg, num: "02", title: "T", body: "B")', True),
    ("point-bare", '#point(title: "T")', False),
    ("data", f'#data(handle: "@t", n: 3, of: 4, title: "T", rows: {rows})', False),
    ("data-empty", '#data(title: "T")', False),
    ("cta", '#cta(handle: "@t", n: 4, of: 4, bg: bg, title: "T", ask: "A")', True),
):
    src, png = slide / f"{name}.typ", slide / f"{name}.png"
    src.write_text(plan.typst_source(markup, has_bg))
    sh(plan.typst_argv(str(slide), str(src), str(png)))
    size = ffprobe(png, "stream=width,height")["streams"][0]
    assert (size["width"], size["height"]) == (1080, 1350), (name, size)

# Contact sheet: two clips and a photo. Needs drawtext (libfreetype + fontconfig) and Inter.
sh([*gen, "testsrc2=size=360x640:rate=25:duration=2", "-c:v", "libx264", str(work / "tall.mp4")])
assets = [
    plan.Preview("a", str(sdr), True, probes[0].duration, "landscape"),
    plan.Preview("b", str(work / "tall.mp4"), True, 2.0, "portrait"),
    plan.Preview("c", str(bg), False, 0, "portrait"),
]
tiles = work / "tiles"
tiles.mkdir()
for argv in plan.tile_argvs(assets, str(tiles)):
    sh(argv)
sheet = work / "sheet.jpg"
sh(plan.sheet_argv(str(tiles), len(assets), str(sheet)))
s = ffprobe(sheet, "stream=codec_name,width,height")["streams"][0]
assert (s["codec_name"], s["width"], s["height"]) == ("mjpeg", 1536, 512), s
print(plan.legend(assets))
print("sheet", s)

# inspect_clip: sheet and per-second table, with and without audio, SDR and HDR, mid-clip start.
for clip, has_audio, portrait, is_hdr in (
    (sdr, True, False, False),
    (work / "tall.mp4", False, True, False),
    (hdr, False, False, True),
):
    sheet, vstats, astats, trf = (work / n for n in ("insp.jpg", "v.txt", "a.txt", "c.trf"))
    sh(
        plan.inspect_video_argv(
            str(clip), 0.5, 1.5, portrait, is_hdr, *map(str, (sheet, vstats, trf))
        )
    )
    video = plan.parse_metadata(vstats.read_text())
    plan.add_camera(video, trf.read_text(), plan.inspect_tile(portrait)[0])
    audio = None
    if has_audio:
        sh(plan.inspect_audio_argv(str(clip), 0.5, 1.5, str(astats)))
        audio = plan.parse_metadata(astats.read_text())
    table = plan.inspect_table(0.5, 1.5, video, audio)
    print(table)
    rows = [r.split() for r in table.splitlines()[1:]]
    assert [r[0] for r in rows] == ["0.5", "1.5"], table
    assert all(len(r) == 7 and "-" not in r[4:] for r in rows), table
    s = ffprobe(sheet, "stream=width,height")["streams"][0]
    print("inspect sheet", s)
    assert s["height"] == (240 if portrait else 134), s


# Memory: one 4K HLG 10-bit clip. The old single-run design measured about 1200 MB on three
# such clips, and grew with the segment count; each segment is now its own run.
def peak_rss_mb(argv):
    pid = os.posix_spawnp(argv[0], argv, os.environ)
    _, status, usage = os.wait4(pid, 0)
    assert os.waitstatus_to_exitcode(status) == 0, argv
    return usage.ru_maxrss // 1024  # KB on Linux


# H.264 High10 rather than HEVC: libx265 at 4K needs more RAM than a small Colima VM has.
codec = ["-c:v", "libx264", "-profile:v", "high10", "-preset", "ultrafast", "-threads", "1"]
big = work / "big.mp4"
sh([*gen, "testsrc2=size=3840x2160:rate=30:duration=3", "-f", "lavfi", "-i", "sine=duration=3",
    "-pix_fmt", "yuv420p10le", *codec, "-colorspace", "bt2020nc", "-color_primaries", "bt2020",
    "-color_trc", "arib-std-b67", "-c:a", "aac", "-shortest", str(big)])  # fmt: skip
big_probe = plan.parse_probe(json.loads(sh(plan.probe_argv(str(big)))))
assert big_probe.hdr
peak = peak_rss_mb(plan.segment_argv(str(big), 0.5, 3, big_probe, True, str(work / "big1.mkv")))
print(f"4K segment peak RSS {peak} MB")
assert peak < 1024, peak
(work / "big.txt").write_text(plan.concat_list(["big1.mkv", "big1.mkv"]))
peak = peak_rss_mb(plan.concat_argv(str(work / "big.txt"), str(work / "bigreel.mp4")))
print(f"concat peak RSS {peak} MB")
assert peak < 512, peak
print("smoke ok")
