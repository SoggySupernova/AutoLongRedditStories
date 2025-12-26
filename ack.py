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

audio_path = "temp/merged.wav"
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
text = "".join(line for line in lines).replace("\n", " ").strip()

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

def json_to_srt(data: List[Dict], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        for idx, item in enumerate(data, start=1):
            start_time = seconds_to_srt_time(item["start"])
            end_time = seconds_to_srt_time(item["end"])
            text = item["text"]

            f.write(f"{idx}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")

if __name__ == "__main__":

    json_to_srt(word_timestamps, "temp/output.srt")
