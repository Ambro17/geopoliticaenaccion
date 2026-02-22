#!/usr/bin/env python
"""
Minimal PoC: transcribe an audio file to text using faster-whisper.

Usage:
    source .venv/bin/activate
    python transcribe.py Venezuela.mp3
"""

from __future__ import annotations
import time
import argparse
import sys
import os
from pathlib import Path

from faster_whisper import WhisperModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe audio to text with faster-whisper.")
    parser.add_argument(
        "audio_path",
        type=Path,
        help="Path to an audio file (mp3, wav, m4a, etc.).",
    )
    parser.add_argument(
        "--model",
        default="medium",
        help="Whisper model size to use (tiny, base, small, medium, large-v3).",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Device to run on (cpu, cuda). Keep cpu for portability.",
    )
    parser.add_argument(
        "--language",
        default="es",
        help="Force a language code (e.g. es, en). If omitted, language is detected.",
    )
    parser.add_argument(
        "--compute-type",
        default="int8",
        help="Quantization type (int8, int8_float16, float16, float32).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Where to save the transcript.",
    )
    parser.add_argument(
        "--progress",
        dest="progress",
        action="store_true",
        default=True,
        help="Show progress updates while transcribing.",
    )
    parser.add_argument(
        "--no-progress",
        dest="progress",
        action="store_false",
        help="Disable progress updates.",
    )
    parser.add_argument(
        "--cpu-threads",
        type=int,
        default=os.cpu_count(),
        help="Number of threads to use for CPU inference (defaults to all cores).",
    )
    parser.add_argument(
        "--no-vad",
        dest="vad_filter",
        action="store_false",
        help="Disable Voice Activity Detection (VAD) filtering (enabled by default).",
    )
    parser.set_defaults(vad_filter=True)

    return parser.parse_args()


def transcribe_audio(audio_path, model_size="tiny", device="cpu", language="es", compute_type="int8", cpu_threads=None, output_path=None, progress=True, vad_filter=True):
    start = time.time()
    audio_path = Path(audio_path)
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    if cpu_threads is None:
        cpu_threads = os.cpu_count()
        
    print(f"Using device: {device} with {cpu_threads} threads.")

    model = WhisperModel(
        model_size, 
        device=device, 
        compute_type=compute_type,
        cpu_threads=cpu_threads
    )

    segments, info = model.transcribe(
        str(audio_path),
        language=language,
        vad_filter=vad_filter,
        initial_prompt="Diálogo en español rioplatense, acentos y modismos argentinos. Ignorar disfluencias como 'eh', 'ah', 'uh', 'mmm', etc.",
    )
    print(f"Detected language: {info.language} (prob {info.language_probability:.2f})")
    
    total_duration = getattr(info, "duration", None)
    last_reported_percent = -1.0
    last_reported_time = -1.0

    if output_path is None:
        filename = audio_path.stem
        output_path = Path(f"./artifacts/{filename}.txt")
    else:
        output_path = Path(output_path)
        
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for segment in segments:
            text = segment.text.strip()
            print(f"[{segment.start:6.2f}s -> {segment.end:6.2f}s] {text}")
            handle.write(text + "\n")
            if progress:
                if total_duration:
                    percent = min(100.0, (segment.end / total_duration) * 100.0)
                    if percent - last_reported_percent >= 1.0 or segment.end - last_reported_time >= 30.0:
                        print(
                            f"Progress: {percent:5.1f}% ({segment.end:,.1f}s / {total_duration:,.1f}s)",
                            file=sys.stderr,
                        )
                        last_reported_percent = percent
                        last_reported_time = segment.end
                else:
                    if segment.end - last_reported_time >= 30.0:
                        print(f"Progress: {segment.end:,.1f}s processed", file=sys.stderr)
                        last_reported_time = segment.end

    print(f"\nTranscript saved to: {output_path.resolve()}")
    end = time.time()
    in_minutes = int((end - start) / 60)
    print(f"Time taken: {in_minutes} minutes")
    return output_path

def main() -> None:
    args = parse_args()
    transcribe_audio(
        audio_path=args.audio_path,
        model_size=args.model,
        device=args.device,
        language=args.language,
        compute_type=args.compute_type,
        cpu_threads=args.cpu_threads,
        output_path=args.output,
        progress=args.progress,
        vad_filter=args.vad_filter
    )

if __name__ == "__main__":
    main()
