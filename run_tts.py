print("")
print("================================")
print("Generating TTS...")
print("================================")
print("")
print("Loading model...")
from chatterbox.tts_turbo import ChatterboxTurboTTS
import torchaudio as ta
import torch
import re
import os
from pydub import AudioSegment
import subprocess
import sys


scriptfile = open("temp/allstory.txt","r")
script = scriptfile.read()
scriptfile.close()





def split_into_groups(text, min_words=10):
    """
    Split text into sentence groups where each group has at least `min_words`
    words, and no group is longer than necessary.
    """
    # Basic sentence splitting (., ?, ! followed by whitespace)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    groups = []
    current_group = []
    current_word_count = 0

    for sentence in sentences:
        words_in_sentence = len(sentence.split())

        current_group.append(sentence)
        current_word_count += words_in_sentence

        if current_word_count >= min_words:
            groups.append(" ".join(current_group))
            current_group = []
            current_word_count = 0

    # If leftover sentences remain, append them to the last group
    if current_group:
        if groups:
            groups[-1] += " " + " ".join(current_group)
        else:
            groups.append(" ".join(current_group))

    return groups



# Load the Turbo model
model = ChatterboxTurboTTS.from_pretrained(device="cpu")


def generate_audio(text, outputfile):
    # Generate with Paralinguistic Tags
    wav = model.generate(text, audio_prompt_path="input/thirteen.wav") # are you serious, it was commented out THIS WHOLE TIME????
    # wav = model.generate(text)
    ta.save(outputfile, wav, model.sr)



result = split_into_groups(script)
print("")
print(f"Total number of groups: {len(result)}. Estimated time {len(result)*10}sec")
for i, group in enumerate(result, 1):
    print("")
    print(f"Group {i}: ({len(group.split())} words)")
    print(group)
    generate_audio(group, f"temp/tts_snippets/{i}_generated.wav")




print("")
print("================================")
print("Combining audio...")
print("================================")
print("")

# Combine all audio files together

INPUT_FOLDER = "temp/tts_snippets"
OUTPUT_FILE = "temp/merged.wav"
DELAY_MS = 10
SILENCE_DBFS = -60


def extract_number(filename: str) -> int | None:
    match = re.match(r"(\d+)_generated\.wav$", filename)
    return int(match.group(1)) if match else None




def combineaudio():
    files = []

    for name in os.listdir(INPUT_FOLDER):
        number = extract_number(name)
        if number is not None:
            files.append((number, name))

    if not files:
        raise RuntimeError("No valid '*_generated.wav' files found.")

    # Sort numerically, not alphabetically
    files.sort(key=lambda x: x[0])

    silence = AudioSegment.silent(duration=DELAY_MS)
    merged = AudioSegment.empty()

    for index, filename in files:
        path = os.path.join(INPUT_FOLDER, filename)
        audio = AudioSegment.from_wav(path)

        if len(merged) > 0:
            merged += silence

        merged += audio

        print(f"Added: {filename}")

    merged.export(OUTPUT_FILE, format="wav")
    print(f"\nMerged file written to: {OUTPUT_FILE}")


combineaudio()







# speed up audio by 10% (the slower audio works better with the TTS)
print("")
print("================================")
print("Speeding up audio...")
print("================================")
print("")
subprocess.run([
    "ffmpeg", "-i", "temp/merged.wav", "-y", 
    "-af", "asetrate=24000*1.1,aresample=24000", 
    "temp/spedup.wav"
])



# Generate subtitles TXT file by putting every word on a new line

with open("temp/subtitles.txt", "w", encoding="utf-8") as f:
    for word in script.split():
        f.write(word + "\n\n")
        print(word)



# run the align subtitles script

print("")
print("================================")
print("Aligning subtitles...")
print("================================")
print("")


# Old aeneas method:
# subprocess.run(["wsl", "-e", "bash", "-c", "\"./align_subtitles.sh\""])

subprocess.run([sys.executable, "ack.py"])



# trim and add audio to the video

print("")
print("================================")
print("Preparing video...")
print("================================")
print("")
subprocess.run(["ffmpeg", "-ss", "00:01:00", "-to", "00:01:05", "-i", "input/source.mkv", "-c", "copy", "-y", "-avoid_negative_ts", "make_zero", "temp/trimmed.mp4"])
subprocess.run(["ffmpeg", "-i", "temp/trimmed.mp4", "-i", "temp/merged.wav", "-y", "-c:v", "copy", "-c:a", "aac", "-strict", "experimental", "temp/audio_added.mp4"])

# run the python script in the venv
print("")
print("================================")
print("Rendering video...")
print("This is the last step I promise")
print("================================")
print("")
subprocess.run([sys.executable, "add_subtitles.py", "temp/audio_added.mp4", "temp/output.srt", "temp/subtitles_added.mp4"])
