import torch
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
device = "cuda" if torch.cuda.is_available() else "cpu"
batch_size = 16


alignment_model, alignment_tokenizer = load_alignment_model(
    device,
    dtype=torch.float16 if device == "cuda" else torch.float32,
)

audio_waveform = load_audio(audio_path, alignment_model.dtype, alignment_model.device)


with open(text_path, "r") as f:
    lines = f.readlines()
text = "".join(line for line in lines).replace("\n", " ").strip().replace("’","'") # Flatten smart quotes to fix encoding errors, will need to do more in the future

emissions, stride = generate_emissions(
    alignment_model, audio_waveform, batch_size=batch_size
)

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


if __name__ == "__main__":

    json_to_srt(word_timestamps, "temp/output.srt", speed_multiplier=1.15) # so for some reason 1.1 doesn't work but 1.15 does???
