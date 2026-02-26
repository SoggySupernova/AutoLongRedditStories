import subprocess
import sys
import os
import time

print("Setting up folders...")
try:
    os.mkdir("input")
except FileExistsError:
    print("input directory already exists, ignoring.")

try:
    os.mkdir("output")
except FileExistsError:
    print("output directory already exists, ignoring.")


try:
    os.makedirs("temp/tts_snippets")
except FileExistsError:
    print("temp directory already exists, ignoring.")




print("\nWelcome to AutoLongRedditStories!")
print("Loading...")
time.sleep(0.8) # arbitrary time delay to make it feel like it's doing something. It's all about the pyschology you know


def gen_script():
    try:
        subprocess.run(
            [sys.executable, "generate_script.py"],
            check=True,           # raises CalledProcessError on non‑zero exit
        )
    except subprocess.CalledProcessError as e:
        print(f"Child failed with code {e.returncode}", file=sys.stderr)
        print("\n\n\n\nThis is most likely because Ollama is not running. Try running 'ollama serve' or 'sudo systemctl enable --now ollama' in a separate window.")
        sys.exit(e.returncode)   # stop parent script


print("================================")
print("Generating script...")
print("================================")


if "--skip-script-generation" in sys.argv:
    print("Skipping script generation")
else:
    # Generate script, run venv python
    gen_script()


print("")
print("================================")
print("Generating TTS...")
print("================================")
print("")
if "--skip-tts" in sys.argv:
    print("Skipping TTS")
else:
    print("Loading model...")
from chatterbox.tts_turbo import ChatterboxTurboTTS
import torchaudio as ta
import torch
import re
from pydub import AudioSegment
from pathlib import Path



# todo: document this

if "--skip-tts" in sys.argv:
    print("Keeping TTS snippets...")
else:
    # Remove old TTS snippets
    [f.unlink() for f in Path("temp/tts_snippets").glob("*") if f.is_file()]


scriptfile = open("temp/allstory.txt","r")
script = scriptfile.read().replace(" –", "–") # Fix spaces between em dashes
scriptfile.close()





def split_into_groups(text, min_words=10):
    """
    Split text into sentence groups where each group has at least `min_words`
    words, and no group is longer than necessary.
    """
    # Basic sentence splitting (., ?, ! followed by whitespace)
    sentences = re.split(r'(?<!\bDr\.)(?<!\bMr\.)(?<!\bMs\.)(?<!\bMrs\.)(?<!\bProf\.)(?<=[.!?])\s+', text.strip())
    # Experimental regex

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
if "--skip-tts" in sys.argv:
    print("Skipping TTS model loading")
else:
    model = ChatterboxTurboTTS.from_pretrained(device="cpu")


def generate_audio(text, outputfile):
    # Generate with Paralinguistic Tags
    wav = model.generate(text, audio_prompt_path="input/thirteen.wav") # are you serious, it was commented out THIS WHOLE TIME????
    # wav = model.generate(text)
    ta.save(outputfile, wav, model.sr)

if "--skip-tts" in sys.argv:
    print("Skipping TTS generation")
else:
    result = split_into_groups(script)
    print("")
    for a in result:
        print(a)
    print(f"Total number of groups: {len(result)}. Estimated time {len(result)*10}sec")
    for i, group in enumerate(result, 1):
        print("")
        print(f"Group {i}/{len(result)}: {len(group.split())} words")
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

if "--skip-tts" in sys.argv:
    print("Using previous merged audio")
else:
    combineaudio()







# speed up audio by 10% (the slower audio works better with the TTS) (Is not skipped by --skip-tts)
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

if "--skip-subtitle-alignment" in sys.argv:
    print("Skipping subtitle alignment")
else:
    subprocess.run([sys.executable, "align_subtitles.py"]) # Todo: do this in chunks if needed



# trim and add audio to the video

print("")
print("================================")
print("Preparing video...")
print("================================")
print("")
subprocess.run(["ffmpeg", "-ss", "00:01:00", "-to", "00:30:00", "-i", "input/source.mkv", "-c", "copy", "-y", "-avoid_negative_ts", "make_zero", "temp/trimmed.mp4"]) # todo: trim based on length of audio
subprocess.run(["ffmpeg", "-i", "temp/trimmed.mp4", "-i", "temp/spedup.wav", "-y", "-c:v", "copy", "-c:a", "aac", "-shortest", "temp/audio_added.mp4"])

# add captions to the video
print("")
print("================================")
print("Rendering video...")
print("This is the last step I promise")
print("================================")
print("")



# old slow method
# subprocess.run([sys.executable, "add_subtitles.py", "temp/audio_added.mp4", "temp/output.srt", "temp/subtitles_added.mp4"])

if "--no-overwrite-output" in sys.argv:
    subprocess.run(["ffmpeg", "-i", "temp/audio_added.mp4", "-y", "-vf", "subtitles=temp/output.ass:fontsdir=./input", "-c:a", "copy", "-preset", "ultrafast", "-threads", "12", "-crf", "21", "-shortest", "output/temp.mp4"])
else:
    subprocess.run(["ffmpeg", "-i", "temp/audio_added.mp4", "-y", "-vf", "subtitles=temp/output.ass:fontsdir=./input", "-c:a", "copy", "-preset", "ultrafast", "-threads", "12", "-crf", "21", "-shortest", "output/output.mp4"])
    print("Overwriting output warning!")


print("")
print("Finished!")
print("Final video has been saved to output/output.mp4")
