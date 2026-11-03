#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["faster-whisper>=1.1"]
# ///
"""Transcreve um arquivo de áudio com faster-whisper (local).

Saída (stdout): {"language": "pt", "segments": [[início_seg, "texto"], ...]}
Usado pelo `ytvault.py ingest --whisper` quando o vídeo não tem legendas.
"""
import argparse
import json
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--model", default="small")
    ap.add_argument("--language", default=None, help="forçar idioma (ex.: pt); padrão: detectar")
    args = ap.parse_args()

    from faster_whisper import WhisperModel

    model = WhisperModel(args.model, device="auto", compute_type="default")
    segments, info = model.transcribe(args.audio, language=args.language, vad_filter=True)
    out = {"language": info.language, "segments": []}
    for seg in segments:
        out["segments"].append([round(seg.start, 2), seg.text.strip()])
        print(f"  {seg.start:7.1f}s", file=sys.stderr, end="\r")
    json.dump(out, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
