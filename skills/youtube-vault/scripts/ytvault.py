#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["yt-dlp[default]"]
# ///
"""ytvault: parte determinística da skill youtube-vault.

Subcomandos:
  init   <vault>                    cria a estrutura do cofre (não sobrescreve nada)
  ingest <vault> <url|id> [...]     baixa transcrições de vídeos/playlists para raw/
  lint   <vault>                    verifica pendências, duplicatas e links quebrados

A saída para o agente é sempre JSON no stdout; progresso e avisos vão para o stderr.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"

VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
CHANNEL_URL_RE = re.compile(r"youtube\.com/(@|channel/|c/|user/)", re.I)
SENTENCE_END_RE = re.compile(r"[.!?…][\"')\]»”]?$")
CODE_RE = re.compile(r"```.*?```|~~~.*?~~~|`[^`\n]*`", re.S)
WIKILINK_RE = re.compile(r"!?\[\[([^\]|#^]+)(?:[#^][^\]|]*)?(?:\|[^\]]*)?\]\]")

VAULT_DIRS = [
    "raw/transcripts",
    "raw/playlists",
    "wiki/videos",
    "wiki/conceitos",
    "wiki/canais",
    "wiki/pessoas",
]


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def emit(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- formatação

def fmt_ts(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def ts_link(video_id: str, seconds: float) -> str:
    return f"[{fmt_ts(seconds)}](https://youtu.be/{video_id}?t={int(seconds)})"


def yaml_str(value) -> str:
    # String JSON (sem escape de não-ASCII) é um escalar YAML válido entre aspas duplas.
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def fmt_date(upload_date: str | None) -> str | None:
    if upload_date and re.fullmatch(r"\d{8}", upload_date):
        return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    return None


# ---------------------------------------------------------------- legendas

def parse_json3(raw: str) -> list[tuple[float, str]]:
    """Converte legendas json3 do YouTube em [(início_seg, texto)]."""
    data = json.loads(raw)
    out: list[tuple[float, str]] = []
    for ev in data.get("events", []):
        segs = ev.get("segs")
        if not segs:
            continue
        text = " ".join("".join(s.get("utf8", "") for s in segs).split())
        if not text:
            continue
        out.append((ev.get("tStartMs", 0) / 1000.0, text))
    return out


def build_blocks(segments, chapters=None, chunk: float = 45.0):
    """Agrupa segmentos em parágrafos (~chunk s, preferindo fim de frase) e
    insere títulos de capítulo. Retorna [("h", título) | ("p", início, texto)]."""
    chapters = sorted(chapters or [], key=lambda c: c.get("start_time", 0))
    blocks: list[tuple] = []
    ci = 0
    cur: list[str] = []
    cur_start: float | None = None

    def flush():
        nonlocal cur, cur_start
        if cur:
            blocks.append(("p", cur_start, " ".join(cur)))
        cur, cur_start = [], None

    for start, text in segments:
        while ci < len(chapters) and start >= chapters[ci].get("start_time", 0):
            flush()
            blocks.append(("h", chapters[ci].get("title") or f"Capítulo {ci + 1}"))
            ci += 1
        if cur_start is None:
            cur_start = start
        cur.append(text)
        dur = start - cur_start
        if (dur >= chunk and SENTENCE_END_RE.search(text)) or dur >= chunk * 2:
            flush()
    flush()
    return blocks


def pick_track(info: dict, langs: list[str]):
    """Escolhe a melhor faixa de legenda. Prioridade: manual nos idiomas pedidos >
    automática original (ASR) > manual em qualquer idioma > automática traduzida."""
    manual = {k: v for k, v in (info.get("subtitles") or {}).items() if k != "live_chat"}
    auto = info.get("automatic_captions") or {}

    def match(tracks: dict, lang: str):
        for key in tracks:
            if key == lang or key.lower().startswith(lang.lower() + "-"):
                if not key.endswith("-orig"):
                    return key
        return None

    for lang in langs:
        key = match(manual, lang)
        if key:
            return key, manual[key], "manual"
    orig = [k for k in auto if k.endswith("-orig")]
    if orig:
        return orig[0].removesuffix("-orig"), auto[orig[0]], "auto"
    original_lang = info.get("language")
    if original_lang and original_lang in auto:
        return original_lang, auto[original_lang], "auto"
    if manual:
        key = next(iter(manual))
        return key, manual[key], "manual"
    for lang in langs:
        key = match(auto, lang)
        if key:
            return key, auto[key], "auto-translated"
    return None


# ---------------------------------------------------------------- yt-dlp

class _StderrLogger:
    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        log(f"[yt-dlp] {msg}")

    def error(self, msg):
        log(f"[yt-dlp] {msg}")


def _ydl(extra: dict | None = None):
    from yt_dlp import YoutubeDL

    opts = {"quiet": True, "no_warnings": False, "noprogress": True, "logger": _StderrLogger()}
    opts.update(extra or {})
    return YoutubeDL(opts)


def normalize_target(target: str) -> str:
    if VIDEO_ID_RE.match(target):
        return f"https://www.youtube.com/watch?v={target}"
    return target


def expand_target(url: str, no_playlist: bool, limit: int | None):
    """Retorna (metadados_da_playlist | None, [ids de vídeo])."""
    if CHANNEL_URL_RE.search(url) and "list=" not in url:
        raise ValueError("canais ainda não são suportados nesta versão; use um vídeo ou playlist")
    with _ydl({"extract_flat": "in_playlist", "noplaylist": no_playlist}) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("_type") != "playlist":
        return None, [info["id"]]
    ids = [e["id"] for e in (info.get("entries") or []) if e and e.get("id")]
    if limit:
        ids = ids[:limit]
    meta = {
        "id": info.get("id"),
        "title": info.get("title"),
        "url": info.get("webpage_url") or url,
        "channel": info.get("channel") or info.get("uploader"),
        "entries": [
            {"id": e["id"], "title": e.get("title")}
            for e in (info.get("entries") or [])
            if e and e.get("id") in ids
        ],
    }
    return meta, ids


def fetch_subtitles(ydl, info: dict, langs: list[str]):
    picked = pick_track(info, langs)
    if not picked:
        return None
    lang, formats, source = picked
    fmt = next((f for f in formats if f.get("ext") == "json3"), None)
    if not fmt:
        return None
    raw = ydl.urlopen(fmt["url"]).read().decode("utf-8")
    segments = parse_json3(raw)
    return (lang, source, segments) if segments else None


def whisper_transcribe(video_url: str, model: str, tmp: Path):
    if not shutil.which("uv"):
        raise RuntimeError("uv não encontrado no PATH (necessário para o fallback Whisper)")
    with _ydl({"format": "bestaudio/best", "outtmpl": str(tmp / "%(id)s.%(ext)s")}) as ydl:
        info = ydl.extract_info(video_url, download=True)
        audio = ydl.prepare_filename(info)
    log(f"  transcrevendo áudio com faster-whisper ({model})...")
    proc = subprocess.run(
        ["uv", "run", "--script", str(HERE / "transcribe.py"), audio, "--model", model],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"transcribe.py falhou: {proc.stderr.strip()[-500:]}")
    data = json.loads(proc.stdout)
    return data.get("language"), "whisper", [(s, t) for s, t in data["segments"] if t]


# ---------------------------------------------------------------- notas

def render_transcript(info: dict, lang: str, source: str, segments, chunk: float) -> str:
    vid = info["id"]
    fm = {
        "type": "transcript",
        "video_id": vid,
        "url": f"https://www.youtube.com/watch?v={vid}",
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "channel_url": info.get("channel_url") or info.get("uploader_url"),
        "published": fmt_date(info.get("upload_date")),
        "duration": fmt_ts(info["duration"]) if info.get("duration") else None,
        "language": lang,
        "transcript_source": source,
        "fetched": dt.date.today().isoformat(),
    }
    lines = ["---"]
    for k, v in fm.items():
        lines.append(f"{k}: {yaml_str(v) if v is not None else 'null'}")
    tags = info.get("tags") or []
    lines.append("yt_tags: [" + ", ".join(yaml_str(t) for t in tags[:30]) + "]")
    lines += ["---", "", f"# {info.get('title') or vid}", ""]

    desc = (info.get("description") or "").strip()
    if desc:
        lines += ["## Descrição", "", desc, ""]

    lines += ["## Transcrição", ""]
    for block in build_blocks(segments, info.get("chapters"), chunk):
        if block[0] == "h":
            lines += [f"### {block[1]}", ""]
        else:
            _, start, text = block
            lines += [f"{ts_link(vid, start)} {text}", ""]
    return "\n".join(lines).rstrip() + "\n"


def render_playlist(meta: dict) -> str:
    lines = [
        "---",
        "type: playlist",
        f"playlist_id: {yaml_str(meta['id'])}",
        f"url: {yaml_str(meta['url'])}",
        f"title: {yaml_str(meta['title'])}",
        f"channel: {yaml_str(meta.get('channel'))}",
        f"fetched: {yaml_str(dt.date.today().isoformat())}",
        "---",
        "",
        f"# {meta['title']}",
        "",
    ]
    for i, e in enumerate(meta["entries"], 1):
        lines.append(f"{i}. [[{e['id']}|{e.get('title') or e['id']}]]")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- comandos

def cmd_init(args) -> int:
    vault = Path(args.vault).expanduser().resolve()
    created = []
    for d in VAULT_DIRS:
        p = vault / d
        if not p.exists():
            p.mkdir(parents=True)
            created.append(d + "/")
    files = {
        "AGENTS.md": (ASSETS / "AGENTS.md").read_text(encoding="utf-8"),
        "CLAUDE.md": "@AGENTS.md\n",
        "index.md": "# Índice\n\nMapa do conteúdo do cofre. Mantido pelo agente.\n\n## Canais\n\n## Playlists\n\n## Conceitos\n",
        "log.md": "# Log\n\nRegistro cronológico de ingestões e revisões (mais recente no topo).\n",
    }
    for name, content in files.items():
        p = vault / name
        if not p.exists():
            p.write_text(content, encoding="utf-8")
            created.append(name)
    emit({"vault": str(vault), "created": created})
    return 0


def cmd_ingest(args) -> int:
    vault = Path(args.vault).expanduser().resolve()
    if not (vault / "raw/transcripts").is_dir():
        log(f"cofre não inicializado em {vault}; rode `init` primeiro")
        return 2
    langs = [l.strip() for l in args.lang.split(",") if l.strip()]
    results, playlists = [], []

    with tempfile.TemporaryDirectory() as tmpdir, _ydl() as ydl:
        tmp = Path(tmpdir)
        for target in args.targets:
            url = normalize_target(target)
            try:
                meta, ids = expand_target(url, args.no_playlist, args.limit)
            except Exception as e:  # noqa: BLE001
                results.append({"target": target, "status": "error", "error": str(e)})
                continue
            if meta:
                path = vault / "raw/playlists" / f"{meta['id']}.md"
                path.write_text(render_playlist(meta), encoding="utf-8")
                playlists.append({"id": meta["id"], "title": meta["title"],
                                  "path": str(path.relative_to(vault)), "videos": len(ids)})

            for vid in ids:
                out = vault / "raw/transcripts" / f"{vid}.md"
                if out.exists() and not args.force:
                    results.append({"video_id": vid, "status": "skipped", "path": str(out.relative_to(vault))})
                    continue
                log(f"→ {vid}")
                try:
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
                    got = fetch_subtitles(ydl, info, langs)
                    if not got and args.whisper:
                        got = whisper_transcribe(info["webpage_url"], args.whisper_model, tmp)
                    if not got:
                        results.append({"video_id": vid, "title": info.get("title"), "status": "no_transcript",
                                        "error": "sem legendas; rode de novo com --whisper"})
                        continue
                    lang, source, segments = got
                    out.write_text(render_transcript(info, lang, source, segments, args.chunk), encoding="utf-8")
                    results.append({"video_id": vid, "title": info.get("title"),
                                    "channel": info.get("channel") or info.get("uploader"),
                                    "status": "ok", "language": lang, "source": source,
                                    "path": str(out.relative_to(vault))})
                except Exception as e:  # noqa: BLE001
                    results.append({"video_id": vid, "status": "error", "error": str(e).strip()[:500]})

    emit({"vault": str(vault), "playlists": playlists, "results": results})
    ok = any(r["status"] in ("ok", "skipped") for r in results)
    return 0 if ok or not results else 1


def read_frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    fm = {}
    for line in text[3:end if end != -1 else 0].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm


def cmd_lint(args) -> int:
    vault = Path(args.vault).expanduser().resolve()
    md_files = [p for p in vault.rglob("*.md") if not any(part.startswith(".") for part in p.relative_to(vault).parts)]
    all_names = {p.stem.lower() for p in md_files}
    all_files = {p.name.lower() for p in vault.rglob("*") if p.is_file()}

    raw_ids = {p.stem for p in (vault / "raw/transcripts").glob("*.md")}
    wiki_by_id: dict[str, list[str]] = {}
    for p in (vault / "wiki").rglob("*.md") if (vault / "wiki").is_dir() else []:
        vid = read_frontmatter(p).get("video_id")
        if vid:
            wiki_by_id.setdefault(vid, []).append(str(p.relative_to(vault)))

    broken, inbound = [], {p.stem.lower(): 0 for p in md_files}
    for p in md_files:
        text = CODE_RE.sub("", p.read_text(encoding="utf-8", errors="replace"))
        for m in WIKILINK_RE.finditer(text):
            target = m.group(1).strip()
            base = target.rsplit("/", 1)[-1].lower()
            if base in all_names:
                if base != p.stem.lower():
                    inbound[base] += 1
            elif base not in all_files and base.removesuffix(".md") not in all_names:
                broken.append({"file": str(p.relative_to(vault)), "link": target})

    orphans = [
        str(p.relative_to(vault)) for p in md_files
        if p.relative_to(vault).parts[0] == "wiki" and inbound.get(p.stem.lower(), 0) == 0
    ]
    report = {
        "vault": str(vault),
        "pending_transcripts": sorted(raw_ids - wiki_by_id.keys()),
        "wiki_without_transcript": sorted(set(wiki_by_id) - raw_ids),
        "duplicate_video_notes": {k: v for k, v in wiki_by_id.items() if len(v) > 1},
        "broken_links": broken,
        "orphan_notes": sorted(orphans),
    }
    emit(report)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ytvault", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="cria a estrutura do cofre")
    p.add_argument("vault")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("ingest", help="baixa transcrições de vídeos e playlists")
    p.add_argument("vault")
    p.add_argument("targets", nargs="+", help="URL de vídeo/playlist ou ID de vídeo")
    p.add_argument("--lang", default="pt,en", help="idiomas preferidos, em ordem (padrão: pt,en)")
    p.add_argument("--whisper", action="store_true", help="transcrever o áudio quando não houver legenda")
    p.add_argument("--whisper-model", default="small", help="modelo faster-whisper (padrão: small)")
    p.add_argument("--chunk", type=float, default=45.0, help="segundos aproximados por parágrafo")
    p.add_argument("--limit", type=int, help="máximo de vídeos por playlist")
    p.add_argument("--no-playlist", action="store_true", help="em URL watch?v=..&list=.., pegar só o vídeo")
    p.add_argument("--force", action="store_true", help="baixar de novo transcrições já existentes")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("lint", help="verifica a saúde do cofre")
    p.add_argument("vault")
    p.set_defaults(func=cmd_lint)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
