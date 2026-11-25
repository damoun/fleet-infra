"""Run inside the image: render generated clips and a Typst slide, then check the outputs.

docker run --rm -v $PWD/tests:/t --entrypoint python studio-mcp:test /t/smoke.py
"""

import json
import subprocess
import tempfile
import time
from pathlib import Path

from studio_mcp import plan

work = Path(tempfile.mkdtemp())


def sh(argv):
    return subprocess.run(argv, check=True, capture_output=True, text=True).stdout


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

parts = [work / "seg01.mkv", work / "seg02.mkv"]
sh(plan.segment_argv(str(sdr), 0.5, 2.5, probes[0], True, str(parts[0])))
sh(plan.segment_argv(str(hdr), 1, 3, probes[1], True, str(parts[1])))
(work / "list.txt").write_text(plan.concat_list([p.name for p in parts]))
out = work / "reel.mp4"
sh(plan.concat_argv(str(work / "list.txt"), str(out)))
v = ffprobe(
    out, "stream=codec_type,codec_name,profile,width,height,pix_fmt,r_frame_rate,sample_rate"
)
print(json.dumps(v["streams"]))
video = next(s for s in v["streams"] if s["codec_type"] == "video")
assert (video["codec_name"], video["width"], video["height"]) == ("h264", 1080, 1920)
assert video["r_frame_rate"] == "30/1" and video["pix_fmt"] == "yuv420p"
assert any(s["codec_type"] == "audio" and s["codec_name"] == "aac" for s in v["streams"])

bg = work / "bg.jpg"
sh(plan.still_argv(str(sdr), str(bg), 1))
size = ffprobe(bg, "stream=width,height")["streams"][0]
assert (size["width"], size["height"]) == (1080, 1350)
hdr_still = work / "hdr.jpg"
sh(plan.still_argv(str(hdr), str(hdr_still), 1, hdr=True))
size = ffprobe(hdr_still, "stream=width,height,pix_fmt")["streams"][0]
assert (size["width"], size["height"]) == (1080, 1350), size
src, png = work / "slide.typ", work / "slide.png"
src.write_text(plan.typst_source("#align(center + horizon)[= Hello]", True))
sh(plan.typst_argv(str(work), str(src), str(png)))
size = ffprobe(png, "stream=width,height")["streams"][0]
assert (size["width"], size["height"]) == (1080, 1350)
print(sh(["typst", "fonts"]).split())

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


# Memory: a reel of 4K HLG 10-bit clips must stay bounded, one ffmpeg run per segment.
def peak_rss_mb(argv):
    """Peak resident memory of one process (VmHWM), polled while it runs."""
    proc = subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    peak = 0
    while proc.poll() is None:
        try:
            for line in Path(f"/proc/{proc.pid}/status").read_text().splitlines():
                if line.startswith("VmHWM:"):
                    peak = max(peak, int(line.split()[1]) // 1024)
        except OSError:
            break
        time.sleep(0.05)
    assert proc.wait() == 0, proc.stderr.read().decode()
    return peak


# H.264 High10 rather than HEVC: libx265 at 4K needs more RAM than a small Colima VM has.
codec = ["-c:v", "libx264", "-profile:v", "high10", "-preset", "ultrafast", "-threads", "1"]
clips = []
for i in range(3):
    clip = work / f"k{i}.mp4"
    sh([*gen, "testsrc2=size=3840x2160:rate=30:duration=3", "-f", "lavfi", "-i", "sine=duration=3",
        "-pix_fmt", "yuv420p10le", *codec, "-colorspace", "bt2020nc", "-color_primaries", "bt2020",
        "-color_trc", "arib-std-b67", "-c:a", "aac", "-shortest", str(clip)])  # fmt: skip
    clips.append(clip)
big = [plan.parse_probe(json.loads(sh(plan.probe_argv(str(c))))) for c in clips]
assert all(p.hdr for p in big)

parts = []
for i, (clip, probe) in enumerate(zip(clips, big)):
    part = work / f"big{i}.mkv"
    peak = peak_rss_mb(plan.segment_argv(str(clip), 0.5, 3, probe, True, str(part)))
    print(f"segment {i} peak RSS {peak} MB")
    parts.append(part)
    assert peak < 2048, peak
(work / "big.txt").write_text(plan.concat_list([p.name for p in parts]))
reel = work / "big.mp4"
print(f"concat peak RSS {peak_rss_mb(plan.concat_argv(str(work / 'big.txt'), str(reel)))} MB")
v = ffprobe(reel, "stream=codec_type,codec_name,profile,width,height,r_frame_rate,sample_rate")
print(json.dumps(v["streams"]))
video = next(s for s in v["streams"] if s["codec_type"] == "video")
audio = next(s for s in v["streams"] if s["codec_type"] == "audio")
assert (video["codec_name"], video["profile"], video["width"], video["height"]) == (
    "h264", "High", 1080, 1920,
)  # fmt: skip
assert video["r_frame_rate"] == "30/1"
assert (audio["codec_name"], audio["sample_rate"]) == ("aac", "48000")
total = float(ffprobe(reel, "format=duration")["format"]["duration"])
assert abs(total - 3 * 2.5) < 0.1, total
print(f"4K reel ok, duration {total:.2f}s")
print("smoke ok")
