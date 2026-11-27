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


def test_segment_argv_trims_and_normalizes_one_clip():
    argv = plan.segment_argv("a", 1, 4, SDR, True, "seg01.mkv")
    start = argv.index("-ss")
    assert argv[start : start + 6] == ["-ss", "1.000", "-t", "3.000000", "-i", "a"]
    g = graph(argv)
    assert "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1" in g
    assert "fps=30" in g and "[0:v:0]setpts=PTS-STARTPTS" in g and "loudnorm" not in g
    assert "apad=whole_dur=3.000000,atrim=duration=3.000000,asetpts=PTS-STARTPTS[a]" in g
    # Identical encodes are what lets the concat stage stream-copy the segments.
    for flag in ("libx264", "pcm_s16le", "veryfast"):
        assert flag in argv
    assert argv[argv.index("-crf") + 1] == "16" and argv[-1] == "seg01.mkv"


def test_stabilize_passes_share_the_segment_frames():
    detect = plan.stabilize_argv("a", 1, 4, HDR, "/w/s.trf")
    chain = detect[detect.index("-vf") + 1]
    assert chain.endswith(",vidstabdetect=result=/w/s.trf") and "zscale" in chain
    assert detect[-3:] == ["-f", "null", "-"]
    g = graph(plan.segment_argv("a", 1, 4, HDR, True, "o.mkv", "/w/s.trf"))
    assert g.startswith(f"[0:v:0]{chain.removesuffix(',vidstabdetect=result=/w/s.trf')}")
    assert ",vidstabtransform=input=/w/s.trf:smoothing=15,unsharp=5:5:0.8:3:3:0.4[v]" in g
    seg = plan.segment_argv("a", 1, 4, HDR, True, "o.mkv", "/w/s.trf")
    assert (
        detect[detect.index("-ss") : detect.index("-i") + 2]
        == seg[seg.index("-ss") : seg.index("-i") + 2]
    )
    assert "vidstab" not in graph(plan.segment_argv("a", 1, 4, HDR, True, "o.mkv"))


def test_segment_argv_tonemaps_only_hdr():
    assert "zscale" not in graph(plan.segment_argv("a", 0, 2, SDR, True, "o.mkv"))
    assert "zscale=t=linear" in graph(plan.segment_argv("a", 0, 2, HDR, True, "o.mkv"))


def test_segment_argv_silence_when_no_audio_or_not_kept():
    for probe, keep in [(SDR, False), (HDR, True)]:
        g = graph(plan.segment_argv("a", 0, 2, probe, keep, "o.mkv"))
        assert "anullsrc=r=48000:cl=stereo,atrim=duration=2.000000" in g and "[0:a:0]" not in g


def test_segment_argv_clamps_end_and_rejects_start_past_end():
    argv = plan.segment_argv("a", 15, 99, SDR, True, "o.mkv")
    assert argv[argv.index("-t") + 1] == "5.000000"
    with pytest.raises(ValueError):
        plan.segment_argv("a", 25, 30, SDR, True, "o.mkv")


def test_segment_argv_cuts_on_whole_frames():
    argv = plan.segment_argv("a", 0, 1.01, SDR, True, "o.mkv")  # 30.3 frames -> 30
    assert argv[argv.index("-t") + 1] == "1.000000"
    argv = plan.segment_argv("a", 0, 0.05, SDR, True, "o.mkv")  # 1.5 frames -> 2
    assert argv[argv.index("-t") + 1] == f"{2 / 30:.6f}"
    assert f"atrim=duration={2 / 30:.6f}" in graph(argv)


def test_segment_argv_rejects_sub_frame_segments():
    with pytest.raises(ValueError, match="shorter than one frame"):
        plan.segment_argv("a", 1, 1.01, SDR, True, "o.mkv")


def test_concat_list_and_argv_copy_video_and_normalize_audio_once():
    assert plan.concat_list(["seg01.mkv", "seg02.mkv"]) == "file 'seg01.mkv'\nfile 'seg02.mkv'\n"
    argv = plan.concat_argv("/w/list.txt", "/w/reel.mp4")
    i = argv.index("-f")
    assert argv[i : i + 4] == ["-f", "concat", "-i", "/w/list.txt"] and argv[-1] == "/w/reel.mp4"
    assert argv[argv.index("-c:v") + 1] == "copy"
    assert argv[argv.index("-af") + 1] == "loudnorm=I=-16:TP=-1.5:LRA=11"
    assert "aac" in argv and "+faststart" in argv


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


def test_typst_source_imports_brand_and_sets_bg():
    plain = plan.typst_source("= Hi", False)
    assert plain.startswith('#import "brand.typ": *\n')
    assert "width: 1080pt, height: 1350pt" in plain and "#let bg = none" in plain
    assert plain.endswith("= Hi\n")
    assert '#let bg = "bg.jpg"' in plan.typst_source("#cover(bg: bg)", True)


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


def test_sheet_stays_under_the_vision_embed_size():
    assert plan.PER_ROW * len(plan.FRACTIONS) * plan.TILE <= 1568


def test_unavailable_asset_keeps_three_black_tiles_and_a_legend_line():
    bad = plan.Preview(ID, "", False, 0, None, "HTTPStatusError: 404")
    argvs = plan.asset_tiles(2, bad, "/t")
    assert [a[-1] for a in argvs] == ["/t/t04.png", "/t/t05.png", "/t/t06.png"]
    assert all(a == plan.black_argv(a[-1]) for a in argvs)
    assert plan.legend([PHOTO_PREVIEW, bad]).endswith(f"#2 {ID} unavailable: HTTPStatusError: 404")


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
    Slide(typst="#cover(bg: bg)", background=ID)
    with pytest.raises(ValidationError):
        Slide()
    with pytest.raises(ValidationError):
        Slide(photo=ID, typst="#cover()")


OTHER = "00000001-0000-4000-8000-000000000000"


@pytest.mark.parametrize("markup", [
    '#cover(title: "Hi")', '  #point(title: "T")', '#data(title: "T")', '#cta(title: "T")',
])
def test_typst_slides_accept_a_leading_brand_call(markup):
    Slide(typst=markup)


@pytest.mark.parametrize("markup", [
    "#align(center)[= Hi]",
    '#place(top)[old]\n#cta(title: "x")',
    '// #cover(title: "x")',
    '#cover (title: "x")',
])
def test_typst_slides_reject_raw_typst(markup):
    with pytest.raises(ValidationError, match="raw Typst is not accepted"):
        Slide(typst=markup)


def test_background_and_bg_argument_go_together():
    Slide(typst="#cover(bg: bg)", background=ID)
    for slide in (
        dict(typst='#cover(title: "Hi")', background=ID),
        dict(typst="#cover(bg: none)", background=ID),
        dict(typst="#cover(bg: bg)"),
    ):
        with pytest.raises(ValidationError, match="exactly when"):
            Slide(**slide)


def spec(*slides):
    return CarouselSpec(album="a", caption="c", week="2026-W48", slides=list(slides))


def test_carousel_rejects_a_repeated_image():
    spec(Slide(photo=ID), Slide(typst="#point(bg: bg)", background=OTHER))
    spec(Slide(photo=ID, t=1), Slide(photo=ID, t=5))
    for pair in (
        (Slide(photo=ID), Slide(photo=ID)),
        (Slide(photo=ID), Slide(typst="#point(bg: bg)", background=ID)),
        (Slide(photo=ID), Slide(photo=ID.upper())),
    ):
        with pytest.raises(ValidationError, match=f"repeated: {ID}"):
            spec(*pair)


def test_spec_validation_limits():
    slides = [Slide(photo=f"{n:08d}-0000-4000-8000-000000000000") for n in range(10)]
    CarouselSpec(album="a", caption="c", week="2026-W48", slides=slides)
    with pytest.raises(ValidationError):
        CarouselSpec(album="a", caption="c", week="2026-W48", slides=slides + [Slide(photo=ID)])
    with pytest.raises(ValidationError):
        CarouselSpec(album="a", caption="c", week="2026-48", slides=slides)
    with pytest.raises(ValidationError):
        Segment(asset_id=ID, start=3, end=3)
    with pytest.raises(ValidationError):
        ReelSpec(album="a", caption="c", week="2026-W48", segments=[])


def test_inspect_rate_keeps_half_seconds_then_caps_frames():
    assert [plan.inspect_rate(s) for s in (3, 30, 31, 56, 90, 300)] == [1, 1, 2, 2, 3, 10]


def test_inspect_video_argv_labels_clip_time_and_sizes_the_sheet():
    argv = plan.inspect_video_argv("v", 13.5, 20, True, False, "s.jpg", "/w/v.txt", "/w/c.trf")
    i = argv.index("-ss")
    assert argv[i : i + 6] == ["-ss", "13.500", "-t", "20.000", "-i", "v"]
    g = graph(argv)
    assert "trunc(t+13.500)" in g and "fps=2/1," in g and "zscale" not in g
    assert "tile=10x5[sheet]" in g  # 41 frames at 0.5s, 10 portrait frames a row
    assert "blurdetect,metadata=print:file=/w/v.txt,vidstabdetect=result=/w/c.trf[stats]" in g
    j = argv.index("[sheet]")
    assert argv[j + 1 : j + 5] == ["-frames:v", "1", "-q:v", "3"]
    wide = graph(plan.inspect_video_argv("v", 0, 56, False, True, "s.jpg", "v.txt", "c.trf"))
    assert "zscale=t=linear" in wide and "fps=2/2," in wide and "scale=-2:134," in wide
    assert "tile=6x10[sheet]" in wide  # 57 frames at 1s


def test_parse_metadata_and_table_bucket_by_second_in_clip_time():
    video = plan.parse_metadata(
        "frame:0    pts:0       pts_time:0\ntimecode=01:02:03:04\n"
        "lavfi.signalstats.YAVG=51\nlavfi.signalstats.YDIF=0\nlavfi.blur=5\n"
        "frame:1    pts:512     pts_time:0.5\nlavfi.signalstats.YAVG=153\nlavfi.signalstats.YDIF=4\n"
        "lavfi.blur=nan\n"
        "frame:2    pts:1024    pts_time:1.2\nlavfi.signalstats.YAVG=0\nlavfi.signalstats.YDIF=12.25\n"
    )
    assert video[1][1][plan.YDIF] == 4.0
    audio = plan.parse_metadata(
        "frame:0 pts:0 pts_time:0\nlavfi.r128.M=-120.691\n"
        "frame:1 pts:4800 pts_time:0.1\nlavfi.r128.M=-8.4\n"
        "frame:2 pts:9600 pts_time:1.1\nlavfi.r128.M=-120.7\n"
    )
    table = plan.inspect_table(20, 2, video, audio).splitlines()
    assert table == [
        "t(s) loud(LUFS) bright(%) motion camera(%) shake(%) blur",
        "20 -8 39 2.0 - - 5.0",  # nan blur is skipped
        "21 silent 0 12.2 - - -",
    ]
    assert plan.inspect_table(0, 1, video, None).splitlines()[1] == "0 no-audio 39 2.0 - - 5.0"


def test_add_camera_takes_the_median_move_and_its_jitter_around_half_a_second():
    video = [(t, {plan.YAVG: 16}) for t in (0.0, 0.5, 1.0)]
    trf = (
        "VID.STAB 1\n#      accuracy = 15\nFrame 1 (List 0 [])\n"
        "Frame 2 (List 3 [(LM 2 0 16 16 32 0.5 0.1),(LM 4 0 48 16 32 0.5 0.1),"
        "(LM 3 0 80 16 32 0.5 0.1)])\nFrame 3 (List 0 [])\n"
    )
    plan.add_camera(video, trf, 240)
    # Frame 2 moves 3px; the mean over frames 1-3 is 1px, so it shakes by 2px.
    assert (video[1][1][plan.CAMERA], video[1][1][plan.SHAKE]) == pytest.approx((1.25, 2 / 2.4))
    assert (video[0][1][plan.CAMERA], video[0][1][plan.SHAKE]) == pytest.approx((0, 1.5 / 2.4))
    table = plan.inspect_table(0, 1, video, None).splitlines()[1]
    assert table.split()[4:6] == ["0.6", "0.73"]
