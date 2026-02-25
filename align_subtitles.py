import sys

print("Loading torch...")

import torch

print("Loading model...")
from ctc_forced_aligner import (
    load_audio,
    load_alignment_model,
    generate_emissions,
    preprocess_text,
    get_alignments,
    get_spans,
    postprocess_results,
)


audio_path = "temp/merged.wav" # Use non-sped up version for stability, speed back up later
text_path = "temp/subtitles.txt"
language = "iso" # ISO-639-3 Language code
batch_size = 8 # 4gb of vram in the big 26 🥀


def load_model_with_fallback():
    device = "cuda" if torch.cuda.is_available() else "cpu"

    try:
        print(f"Trying to load model on {device}...")
        model, tokenizer = load_alignment_model(
            device,
            dtype=torch.float16 if device == "cuda" else torch.float32,
        )
        return model, tokenizer, device

    except RuntimeError as e:
        if "out of memory" in str(e).lower() and device == "cuda":
            print("CUDA out of memory. Falling back to CPU...")
            torch.cuda.empty_cache()

            device = "cpu"
            model, tokenizer = load_alignment_model(
                device,
                dtype=torch.float32,
            )
            return model, tokenizer, device
        raise


alignment_model, alignment_tokenizer, device = load_model_with_fallback()

print("Loading audio...")
audio_waveform = load_audio(audio_path, alignment_model.dtype, alignment_model.device)
print("Loaded")

print("\n\n\nProcessing... This may take a while.")

try:
    emissions, stride = generate_emissions(
        alignment_model,
        audio_waveform,
        batch_size=batch_size,
    )

except RuntimeError as e:
    if "out of memory" in str(e).lower() and device == "cuda":
        print("CUDA out of memory. Retrying on CPU...")
        torch.cuda.empty_cache()

        # Move model + audio to CPU
        alignment_model = alignment_model.to("cpu")
        audio_waveform = audio_waveform.to("cpu")

        emissions, stride = generate_emissions(
            alignment_model,
            audio_waveform,
            batch_size=1,  # safer on CPU
        )
    else:
        raise






# Translation table for smart quotes
SMART_QUOTES = {
    ord("“"): '"',
    ord("”"): '"',
    ord("„"): '"',
    ord("‟"): '"',
    ord("‘"): "'",
    ord("’"): "'",
    ord("‚"): "'",
    ord("‛"): "'",
}

EM_DASH = "—"   # U+2014
EN_DASH = "–"   # U+2013

def normalize_text(text: str) -> str:
    text = text.translate(SMART_QUOTES)
    text = text.replace(EM_DASH, ", ")
    text = text.replace(EN_DASH, "-")
    return text





with open(text_path, "r", encoding="utf8") as f:
    lines = f.readlines()
text = "".join(line for line in lines).replace("\n", " ").strip()
text = normalize_text(text).replace('\u2026','...').replace('*','') # I've tried telling it to not use asterisks but it still did adhgsahdfdjfh
print(text)

print("\n\n\n")























tokens_starred, text_starred = preprocess_text(
    text,
    romanize=True,
    language=language,
)


segments, scores, blank_token = get_alignments(
    emissions,
    tokens_starred,
    alignment_tokenizer,
)




spans = get_spans(tokens_starred, segments, blank_token)

word_timestamps = postprocess_results(text_starred, spans, stride, scores)

print(word_timestamps)








import json
from typing import List, Dict

def seconds_to_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def json_to_srt(
    data: List[Dict],
    output_path: str,
    speed_multiplier: float = 1.0
) -> None:
    """
    speed_multiplier > 1.0  -> faster subtitles
    speed_multiplier < 1.0  -> slower subtitles
    """

    # Apply speed multiplier
    scaled = [
        {
            "start": item["start"] / speed_multiplier,
            "end": item["end"] / speed_multiplier,
            "text": item["text"],
        }
        for item in data
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        for i, item in enumerate(scaled):
            start = item["start"]

            # End time = next subtitle's start (except last)
            if i < len(scaled) - 1:
                end = scaled[i + 1]["start"]
            else:
                end = item["end"]

            f.write(f"{i + 1}\n")
            f.write(
                f"{seconds_to_srt_time(start)} --> "
                f"{seconds_to_srt_time(end)}\n"
            )
            f.write(f"{item['text']}\n\n")


json_to_srt(word_timestamps, "temp/output.srt", speed_multiplier=1.1) # 1.15 works better for shorter snippets for some reason






# convert srt to ass

# truly an unfortunate acronym





import sys
import re
from pathlib import Path

from fontTools import ttLib

def get_font_family_name(path: str) -> str | None:
    font = ttLib.TTFont(path)
    # nameID 1 = Font Family name
    return font["name"].getDebugName(1)

fintname = get_font_family_name("input/font.otf") # misspelling intentional
print(f"Font name: {fintname}")


ASS_HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{fintname},150,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,10,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def srt_time_to_ass(time_str: str) -> str:
    h, m, rest = time_str.split(":")
    s, ms = rest.split(",")
    cs = int(ms) // 10  # centiseconds
    return f"{int(h)}:{m}:{s}.{cs:02d}"


def parse_srt(srt_text: str):
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            continue

        time_line = lines[1]
        text_lines = lines[2:]

        start, end = time_line.split(" --> ")
        text = r"\N".join(text_lines)  # ASS newline

        yield (
            srt_time_to_ass(start.strip()),
            srt_time_to_ass(end.strip()),
            text
        )


def convert_srt_to_ass(input_path: Path, output_path: Path):
    srt_text = input_path.read_text(encoding="utf-8")
    events = []

    for start, end, text in parse_srt(srt_text):
        dialogue = (
            f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
        )
        events.append(dialogue)

    ass_content = ASS_HEADER + "\n".join(events) + "\n"
    output_path.write_text(ass_content, encoding="utf-8")


convert_srt_to_ass(Path("temp/output.srt"), Path("temp/output.ass"))
