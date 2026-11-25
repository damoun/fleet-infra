"""Run inside the image: render generated clips and a Typst slide, then check the outputs.

docker run --rm -v $PWD/tests:/t --entrypoint python studio-mcp:test /t/smoke.py
"""

import json
import subprocess
import tempfile
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

probes = [plan.parse_probe(ffprobe(p, "stream=codec_type,color_transfer:format=duration"))
          for p in (sdr, hdr)]  # fmt: skip
assert [p.hdr for p in probes] == [False, True], probes
assert [p.has_audio for p in probes] == [True, False], probes

out = work / "reel.mp4"
sh(plan.reel_argv([(str(sdr), 0.5, 2.5, probes[0]), (str(hdr), 1, 3, probes[1])], True, str(out)))
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
src, png = work / "slide.typ", work / "slide.png"
src.write_text(plan.typst_source("#align(center + horizon)[= Hello]", True))
sh(plan.typst_argv(str(work), str(src), str(png)))
size = ffprobe(png, "stream=width,height")["streams"][0]
assert (size["width"], size["height"]) == (1080, 1350)
print(sh(["typst", "fonts"]).split())
print("smoke ok")
