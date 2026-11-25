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


def test_recent_weeks_window_crosses_year():
    assert plan.recent_weeks(date(2027, 1, 6), 3) == ["2027-W01", "2026-W53", "2026-W52"]
    assert plan.recent_weeks(date(2027, 1, 6), 0) == []


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
        "width": 1440,
        "height": 1920,
        "exifInfo": {"city": "Ibiza", "country": "Spain", "description": "beach"},
        "tags": [{"value": "used/2026-W30"}, {"value": "used/2026-W40"}, {"value": "trip"}],
    }
    assert plan.compact_asset(item) == {
        "id": ID,
        "type": "video",
        "taken_at": "2026-06-01T10:00:00Z",
        "place": "Ibiza, Spain",
        "duration": 12.5,
        "orientation": "portrait",
        "tags": ["trip"],
        "description": "beach",
        "last_used": "2026-W40",
        "use_count": 2,
    }


def test_orientation_uses_rotated_top_level_size():
    assert plan.orientation({"width": 1440, "height": 1920}) == "portrait"
    assert plan.orientation({"width": 1920, "height": 1440}) == "landscape"
    assert plan.orientation({"width": 5, "height": 5}) == "square"
    assert plan.orientation({"width": 5, "height": None}) is None
    assert plan.orientation({}) is None


def test_compact_asset_without_used_tags():
    item = {"id": ID, "type": "IMAGE", "fileCreatedAt": "x", "tags": [{"value": "trip"}]}
    got = plan.compact_asset(item)
    assert (got["last_used"], got["use_count"], got["duration"]) == (None, 0, None)


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
    start = argv.index("-ss")
    assert argv[start : start + 12] == [
        "-ss", "1.000", "-t", "3.000", "-i", "a", "-ss", "0.000", "-t", "2.000", "-i", "b",
    ]  # fmt: skip
    g = graph(argv)
    assert "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1" in g
    assert "fps=30" in g
    assert g.count("v:0]setpts=PTS-STARTPTS") == 2 and g.count(",asetpts=PTS-STARTPTS") == 2
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


def test_still_argv_seeks_and_crops():
    still = plan.still_argv("in", "out.jpg", 2.5)
    assert still[still.index("-ss") + 1] == "2.500"
    assert "crop=1080:1350" in still[still.index("-vf") + 1]


def test_typst_source_page_and_background():
    plain = plan.typst_source("= Hi", False)
    assert "width: 1080pt, height: 1350pt" in plain and "image(" not in plain
    assert plain.endswith("= Hi\n")
    assert 'image("bg.jpg"' in plan.typst_source("= Hi", True)


VIDEO_PREVIEW = plan.Preview(ID, "/w/v", True, 2.0, "portrait")
PHOTO_PREVIEW = plan.Preview(ID, "/w/p", False, 0, "landscape")


def test_frame_times_and_playback_request():
    assert plan.frame_times(2.0) == [0.3, 1.0, 1.7]
    assert plan.preview_request(ID, "VIDEO") == (f"/assets/{ID}/video/playback", {})
    assert plan.preview_request(ID, "IMAGE") == plan.download_request(ID, "IMAGE")


def test_frame_times_stay_inside_short_clips():
    assert plan.frame_times(0.3) == [0.045, 0.05, 0.05]
    assert plan.frame_times(0.2) == [0.0, 0.0, 0.0]


def test_unknown_duration_gives_one_frame_two_black_tiles_and_no_fake_times():
    unknown = plan.Preview(ID, "/w/v", True, 0, "portrait")
    assert plan.frame_times(0) == [0.0]
    argvs = plan.tile_argvs([unknown], "/t")
    assert len(argvs) == 3 and "-ss" in argvs[0] and "-ss" not in argvs[1] + argvs[2]
    assert plan.legend([unknown]) == f"#1 {ID} video portrait duration unknown"


def test_black_argv_matches_the_black_tiles():
    assert plan.black_argv("/t/t05.png") == plan.tile_argvs([PHOTO_PREVIEW], "/t")[1][:-1] + [
        "/t/t05.png"
    ]


def test_tile_argvs_three_tiles_per_asset_label_first_and_black_for_photos():
    argvs = plan.tile_argvs([VIDEO_PREVIEW, PHOTO_PREVIEW], "/t")
    assert [a[-1] for a in argvs] == [f"/t/t0{n}.png" for n in range(1, 7)]
    seeks = [a[a.index("-ss") + 1] if "-ss" in a else None for a in argvs]
    assert seeks == ["0.300", "1.000", "1.700", "0.000", None, None]
    vf = [a[a.index("-vf") + 1] if "-vf" in a else "" for a in argvs]
    assert "drawtext=text='#1'" in vf[0] and "drawtext" not in vf[1] + vf[2]
    assert "drawtext=text='#2'" in vf[3] and vf[1].startswith("scale=256:256")
    assert "pad=256:256" in vf[0]
    assert "color=c=black:s=256x256" in argvs[4] and "color=c=black:s=256x256" in argvs[5]


def test_sheet_argv_rows_follow_asset_count():
    for assets, rows in [(1, 1), (2, 1), (3, 2), (8, 4)]:
        argv = plan.sheet_argv("/t", assets, "o.jpg")
        assert f"tile=6x{rows}" in argv
    assert argv[argv.index("-i") + 1] == "/t/t%02d.png" and argv[-1] == "o.jpg"


def test_legend_lines():
    assert plan.legend([VIDEO_PREVIEW, PHOTO_PREVIEW]) == (
        f"#1 {ID} video portrait 2.0s frames at 0.3/1.0/1.7s\n#2 {ID} image landscape"
    )


def test_asset_ids_are_lowercased():
    assert Segment(asset_id=ID.upper(), start=0, end=1).asset_id == ID


def test_slide_needs_exactly_one_kind():
    Slide(photo=ID)
    Slide(typst="= Hi", background=ID)
    with pytest.raises(ValidationError):
        Slide()
    with pytest.raises(ValidationError):
        Slide(photo=ID, typst="= Hi")


def test_spec_validation_limits():
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
