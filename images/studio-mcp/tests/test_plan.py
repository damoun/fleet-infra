from datetime import date

import pytest
from pydantic import ValidationError

from studio_mcp import plan
from studio_mcp.models import CarouselSpec, ReelSpec, Segment, Slide

ID = "11111111-1111-4111-8111-111111111111"
SDR = plan.Probe(duration=20, hdr=False, has_audio=True)
HDR = plan.Probe(duration=20, hdr=True, has_audio=False)


def graph(argv):
    return argv[argv.index("-filter_complex") + 1]


def test_iso_week_year_boundary():
    assert plan.iso_week(date(2026, 11, 25)) == "2026-W48"
    assert plan.iso_week(date(2027, 1, 1)) == "2026-W53"
    assert plan.iso_week(date(2024, 12, 30)) == "2025-W01"


def test_recent_weeks_window_crosses_year():
    assert plan.recent_weeks(date(2027, 1, 6), 3) == ["2027-W01", "2026-W53", "2026-W52"]
    assert plan.recent_weeks(date(2027, 1, 6), 0) == []


def test_usage_counts_only_used_tags():
    last, count = plan.usage(["used/2026-W40", "trip/ibiza", "used/2026-W48", "used/2026-W02"])
    assert (last, count) == ("2026-W48", 3)
    assert plan.usage(["trip/ibiza"]) == (None, 0)


def test_download_request_uses_preview_for_photos_and_original_for_videos():
    assert plan.download_request(ID, "IMAGE") == (f"/assets/{ID}/thumbnail", {"size": "preview"})
    assert plan.download_request(ID, "VIDEO") == (f"/assets/{ID}/original", {})


def test_search_without_query_is_metadata_with_filters():
    path, body = plan.search_request(
        None, "2026-06-01", "2026-06-30", "Ibiza", "video", ["a"], ["b"], 10
    )
    assert path == "/search/metadata"
    assert body["size"] == 10
    flt = body["filter"]
    assert flt["takenAt"] == {"gte": "2026-06-01T00:00:00.000Z", "lte": "2026-06-30T23:59:59.999Z"}
    assert flt["or"] == [{"city": {"eq": "Ibiza"}}, {"country": {"eq": "Ibiza"}}]
    assert flt["type"] == {"eq": "VIDEO"}
    assert flt["tagIds"] == {"all": ["a"], "none": ["b"]}
    assert "query" not in body


def test_search_with_query_is_smart_and_empty_filter_is_bare():
    path, body = plan.search_request("sunset", None, None, None, None, [], [], 30)
    assert path == "/search/smart"
    assert body == {"filter": {}, "size": 30, "withExif": True, "query": "sunset"}


def test_compact_asset():
    item = {
        "id": ID,
        "type": "VIDEO",
        "fileCreatedAt": "2026-06-01T10:00:00Z",
        "duration": 12500,
        "exifInfo": {"city": "Ibiza", "country": "Spain", "description": "beach"},
        "tags": [{"value": "used/2026-W30"}, {"value": "used/2026-W40"}, {"value": "trip"}],
    }
    assert plan.compact_asset(item) == {
        "id": ID,
        "type": "video",
        "taken_at": "2026-06-01T10:00:00Z",
        "place": "Ibiza, Spain",
        "duration": 12.5,
        "tags": ["trip"],
        "description": "beach",
        "last_used": "2026-W40",
        "use_count": 2,
    }


def test_parse_probe_detects_hdr_and_audio():
    data = {
        "streams": [{"codec_type": "video", "color_transfer": "arib-std-b67"}],
        "format": {"duration": "3.5"},
    }
    assert plan.parse_probe(data) == plan.Probe(3.5, True, False)
    data = {
        "streams": [{"codec_type": "video"}, {"codec_type": "audio"}],
        "format": {"duration": "3.5"},
    }
    assert plan.parse_probe(data) == plan.Probe(3.5, False, True)


def test_reel_argv_trims_normalizes_and_concats():
    argv = plan.reel_argv([("a", 1, 4, SDR), ("b", 0, 2, HDR)], True, "out.mp4")
    assert argv[4:16] == [
        "-ss",
        "1.000",
        "-t",
        "3.000",
        "-i",
        "a",
        "-ss",
        "0.000",
        "-t",
        "2.000",
        "-i",
        "b",
    ]
    g = graph(argv)
    assert "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1" in g
    assert "fps=30" in g
    assert "[1:v:0]" in g and "zscale=t=linear" in g  # HDR clip only
    assert g.count("zscale=t=linear") == 1
    assert "[0:a:0]" in g and g.count("loudnorm") == 1
    assert "anullsrc" in g  # clip b has no audio
    assert "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][ac];[ac]loudnorm=I=-16:TP=-1.5:LRA=11" in g
    assert argv[-1] == "out.mp4"
    for flag in ("libx264", "high", "yuv420p", "aac", "+faststart"):
        assert flag in argv


def test_reel_argv_silence_when_audio_not_kept():
    g = graph(plan.reel_argv([("a", 0, 2, SDR)], False, "o.mp4"))
    assert "anullsrc" in g and "[0:a:0]" not in g


def test_reel_argv_clamps_end_and_rejects_start_past_end():
    argv = plan.reel_argv([("a", 15, 99, SDR)], True, "o.mp4")
    assert argv[argv.index("-t") + 1] == "5.000"
    with pytest.raises(ValueError):
        plan.reel_argv([("a", 25, 30, SDR)], True, "o.mp4")


def test_still_tonemaps_only_hdr_sources():
    sdr = plan.still_argv("in", "out.jpg")
    hdr = plan.still_argv("in", "out.jpg", hdr=True)
    assert "zscale" not in sdr[sdr.index("-vf") + 1]
    assert hdr[hdr.index("-vf") + 1].endswith("format=yuvj420p")
    assert "zscale=t=linear" in hdr[hdr.index("-vf") + 1]


def test_still_and_typst_commands():
    still = plan.still_argv("in", "out.jpg", 2.5)
    assert still[still.index("-ss") + 1] == "2.500"
    assert "crop=1080:1350" in still[still.index("-vf") + 1]
    assert plan.typst_argv("/r", "/r/s.typ", "/r/o.png") == [
        "typst", "compile", "--root", "/r", "--format", "png", "--ppi", "72", "/r/s.typ", "/r/o.png",
    ]  # fmt: skip


def test_typst_source_page_and_background():
    plain = plan.typst_source("= Hi", False)
    assert "width: 1080pt, height: 1350pt" in plain and "image(" not in plain
    assert plain.endswith("= Hi\n")
    assert 'image("bg.jpg"' in plan.typst_source("= Hi", True)


def test_slide_needs_exactly_one_kind():
    Slide(photo=ID)
    Slide(typst="= Hi", background=ID)
    with pytest.raises(ValidationError):
        Slide()
    with pytest.raises(ValidationError):
        Slide(photo=ID, typst="= Hi")


def test_carousel_slide_count_and_week_format():
    slides = [Slide(photo=ID)] * 10
    CarouselSpec(album="a", caption="c", week="2026-W48", slides=slides)
    with pytest.raises(ValidationError):
        CarouselSpec(album="a", caption="c", week="2026-W48", slides=slides + [Slide(photo=ID)])
    with pytest.raises(ValidationError):
        CarouselSpec(album="a", caption="c", week="2026-48", slides=slides)
    with pytest.raises(ValidationError):
        Segment(asset_id=ID, start=3, end=3)
    with pytest.raises(ValidationError):
        ReelSpec(album="a", caption="c", week="2026-W48", segments=[])
