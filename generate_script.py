import requests
import json
import os


# clear previous story
with open("temp/allstory.txt","w") as blank:
    blank.write("")


numrounds = 10


# System prompt for story generation
story_system_prompt = """
You are a long-form story generator.
Generate a coherent story segment of about 300 words.
The story should be fiction but plausible—no creepy monsters, fantasy creatures, or impossible environments.
Do NOT include the summary in the story.
Respond ONLY with the new segment of the story.
Do not repeat the previous part of the story in your response.
Do not stray too far from the original theme.
Never use any Markdown styling.
Never use these overused first or last names: Elias, Thorne, Silas, or Blackwood.
"""

# System prompt for summary update
summary_system_prompt = """
You are a story summarizer. Using the existing summary and the new story segment, update the summary to approximately 200 words.

* If no prior summary exists, create a new one (~100 words).
* Use bullet points.
* **MOST IMPORTANT**: Only add or modify information based on the new segment; **do not replace the summary with a recap of the new segment.**
* Remove information only if needed to keep the summary within length, and remove only nonessential details.
* Do not invent details beyond the provided text.
* Include specific names, objects, events, and unresolved plot threads.
* Focus on essential plot progression, character developments, and continuity-critical details.

Respond with the summary only. Do not add commentary or generate new story content.
"""

# Initial user prompt for story generation
story_user_prompt = ""




hook_sentence = "My mom finally admitted why she never lets me drive at night."

theme_sentence = "After your car breaks down, she reveals a past accident seven years ago in the rain that never appeared in any police record."





# Initial empty summary
summary = "No summary yet."

lastsummary = "No summary yet."


# Different prompt for the first time works better with smaller models
story_prompt = f"Round 1 of {numrounds}\n\nWrite the beginning of a new story based on the opener and plot. Let the theme develop over the {numrounds} rounds instead of jumping to the end right away. NEVER use any Markdown styling or any asterisks.\n\nHook sentence: {hook_sentence}\nOverall Plot: {theme_sentence}\nSummary: No summary yet."

# Ollama API settings
url = "http://localhost:11434/api/chat"
options = {"num_gpu": -1, "num_ctx": 65536}
model_name = "gemma3:4b" # ministral-3:8b-instruct-2512-q4_K_M, gemma3:1b, or gemma3:270m for slower machines

def stream_ollama(system, user_prompt):
    """Call Ollama API with streaming and return generated content"""
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt}
        ],
        "stream": True,
        "options": options,
        "keep_alive": 100
    }

    response = requests.post(url, json=data, stream=True)
    result = ""
    for line in response.iter_lines():
        if line:
            try:
                resp = json.loads(line.decode('utf-8'))
                content = resp.get("message", {}).get("content", "")
                if content:
                    print(content, end='', flush=True)
                    result += content
            except Exception:
                continue
    print("\n")
    return result

endingmessage = ""

for round_number in range(1, numrounds + 1):

    if round_number > (numrounds - 2):
        endingmessage = ": Start wrapping up the story"
    if round_number > (numrounds - 1):
        endingmessage = ": Wrap up the story"

    if round_number > 1:
        story_prompt = f"Round {round_number} of {numrounds}{endingmessage}\n\nOverall Plot: {theme_sentence}\n\nSummary of prior events: {lastsummary}\n\n\nPrevious story segment:\n\n\n{story_user_prompt}\n\n\nContinue the story based on the theme, summary, and previous segment." # use older summary to prevent repeated information



    print(f"=== ROUND {round_number}: STORY GENERATION ===\n")
    print(story_prompt)
    print("\n\n\n")
    # Generate story segment
    story_segment = stream_ollama(story_system_prompt, story_prompt)
    
    with open("temp/allstory.txt","a") as finalstory:
        finalstory.write("\n" + story_segment)

    # Update summary using previous summary and new story segment
    summary_prompt = f"Previous Summary: {summary}\n\n\n\nNew Story Segment: {story_segment}\n\n\n\nUpdate the summary."

    print("\n\n\n\n\nUPDATING SUMMARY")
    lastsummary = summary
    print(summary_prompt)
    summary = stream_ollama(summary_system_prompt, summary_prompt)
    
    # Set the new story segment as prompt for next round
    story_user_prompt = story_segment
