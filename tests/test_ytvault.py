"""Testes offline do ytvault (sem rede). Rodar: uv run --with pytest pytest -q"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ytvault", ROOT / "skills/youtube-vault/scripts/ytvault.py")
ytvault = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ytvault)

JSON3 = json.dumps({"events": [
    {"tStartMs": 0, "dDurationMs": 2000},  # sem segs: ignorado
    {"tStartMs": 1000, "segs": [{"utf8": "Olá"}, {"utf8": " mundo."}]},
    {"tStartMs": 3000, "segs": [{"utf8": "\n"}]},  # só quebra de linha: ignorado
    {"tStartMs": 50000, "segs": [{"utf8": "Segunda   parte"}]},
    {"tStartMs": 61000, "segs": [{"utf8": "fim."}]},
]})


def test_parse_json3():
    assert ytvault.parse_json3(JSON3) == [(1.0, "Olá mundo."), (50.0, "Segunda parte"), (61.0, "fim.")]


def test_fmt_ts():
    assert ytvault.fmt_ts(754) == "12:34"
    assert ytvault.fmt_ts(3725) == "1:02:05"


def test_build_blocks_chunks_and_chapters():
    segs = [(0, "a."), (10, "b"), (50, "c."), (60, "d"), (130, "e.")]
    chapters = [{"start_time": 0, "title": "Intro"}, {"start_time": 55, "title": "Meio"}]
    assert ytvault.build_blocks(segs, chapters, chunk=45) == [
        ("h", "Intro"), ("p", 0, "a. b c."), ("h", "Meio"), ("p", 60, "d e."),
    ]


def test_pick_track_priority():
    fmt = [{"ext": "json3", "url": "u"}]
    info = {"subtitles": {"en": fmt, "live_chat": fmt},
            "automatic_captions": {"en-orig": fmt, "pt": fmt}}
    assert ytvault.pick_track(info, ["pt", "en"])[0::2] == ("en", "manual")
    info = {"subtitles": {}, "automatic_captions": {"en-orig": fmt, "pt": fmt}}
    assert ytvault.pick_track(info, ["pt"])[0::2] == ("en", "auto")
    info = {"subtitles": {"pt-BR": fmt}, "automatic_captions": {}}
    assert ytvault.pick_track(info, ["pt"])[0::2] == ("pt-BR", "manual")
    info = {"subtitles": {}, "automatic_captions": {"pt": fmt}}
    assert ytvault.pick_track(info, ["pt"])[0::2] == ("pt", "auto-translated")
    assert ytvault.pick_track({"subtitles": {}, "automatic_captions": {}}, ["pt"]) is None


def test_render_transcript():
    info = {"id": "abcdefghijk", "title": 'Título "x"', "channel": "Canal", "upload_date": "20260501",
            "duration": 754, "description": "desc", "tags": ["ia"], "chapters": None}
    md = ytvault.render_transcript(info, "pt", "manual", ytvault.parse_json3(JSON3), 45)
    assert 'title: "Título \\"x\\""' in md
    assert "published: \"2026-05-01\"" in md
    assert "[00:01](https://youtu.be/abcdefghijk?t=1) Olá mundo." in md


def test_init_and_lint(tmp_path):
    assert ytvault.main(["init", str(tmp_path)]) == 0
    assert (tmp_path / "AGENTS.md").exists() and (tmp_path / "raw/transcripts").is_dir()
    (tmp_path / "raw/transcripts/abcdefghijk.md").write_text("---\nvideo_id: \"abcdefghijk\"\n---\n")
    (tmp_path / "raw/transcripts/zzzzzzzzzzz.md").write_text("---\n---\n")
    (tmp_path / "wiki/videos/Vídeo.md").write_text(
        "---\ntype: video\nvideo_id: \"abcdefghijk\"\n---\n[[abcdefghijk]] [[Conceito X|x]] [[RAG]]\n")
    (tmp_path / "wiki/conceitos/RAG.md").write_text("[[Vídeo]]\n")
    ytvault.main(["lint", str(tmp_path)])


def test_lint_report(tmp_path, capsys):
    test_init_and_lint(tmp_path)
    report = json.loads(capsys.readouterr().out.split("\n}\n", 1)[1])
    assert report["pending_transcripts"] == ["zzzzzzzzzzz"]
    assert report["broken_links"] == [{"file": "wiki/videos/Vídeo.md", "link": "Conceito X"}]
    assert report["orphan_notes"] == []
