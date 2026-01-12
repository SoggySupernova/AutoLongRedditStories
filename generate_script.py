import requests
import json
import os


# clear previous story
with open("temp/allstory.txt","w") as blank:
    blank.write("")


numrounds = 15

def get_last_paragraph(text):
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    return paragraphs[-1] if paragraphs else ""


# System prompt for story generation
story_system_prompt = """
You are a long-form story generator.

**Response Formatting:**
Generate a coherent story segment of about 300 words.
Do NOT include the summary in the story.
Respond ONLY with the new segment of the story.
Do not repeat the previous part of the story in your response.
Never use any Markdown styling.


**Story Style**:
The story should be fiction but plausible—no creepy monsters, fantasy creatures, or impossible environments.
Do not stray too far from the original theme.
**Use the current round number and total number of rounds to pace the story.**
If the story begins to sound abstract, supernatural, or like science fiction, IMMEDIATELY course-correct by returning to concrete actions, dialogue, or physical investigation.
Do not use any quoted dialogue, instead describe what is being said.
For example:
**INSTEAD OF WRITING:** Mr. Henderson said, "I… I was preparing for some routine maintenance!"
**YOU CAN WRITE:** Mr. Henderson said he was only preparing for some routine mainenance.

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




hook_sentence = "The vet asked when my dog started responding to commands in German."





theme_sentence = "The narrator discovers their adopted dog came from a private training program connected to illegal security work."





# Initial empty summary
summary = "No summary yet."



# Different prompt for the first time works better with smaller models
story_prompt = f"Round 1 of {numrounds}\n\nWrite the beginning of a new story based on the opener and plot. **Let the theme and plot develop over the {numrounds} rounds instead of jumping to the end right away. The narrator should not know about the full plot at the beginning.** Do not repeat the hook sentence in the story, but the beginning of the story should take place right after the hook sentence. NEVER use any Markdown styling or any asterisks.\n\nHook sentence: {hook_sentence}\nOverall Plot: {theme_sentence}\nSummary: No summary yet."

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

last_paragraph = ""


for round_number in range(1, numrounds + 1):
    if round_number > (numrounds - 2):
        endingmessage = ": It is almost the end. **PACING (VERY IMPORTANT, TOP PRIORITY): Start wrapping up the story.**"
    if round_number > (numrounds - 1):
        endingmessage = ": This is the last round. **PACING (VERY IMPORTANT, TOP PRIORITY): Wrap up the story. (Not a cliffhanger!). WRAP UP THE STORY.**"

    if round_number > 1:
        story_prompt = f"""Round {round_number} of {numrounds}{endingmessage}

Overall Plot: {theme_sentence}

Current Summary:
{summary}

Last paragraph of previous segment:
{last_paragraph}

Continue the story naturally from the last paragraph.
Let the theme and plot develop over the {numrounds} rounds instead of jumping to the end right away.
The narrator should not know about the full plot at the beginning.
""" # indentation is weird



    print(f"=== ROUND {round_number}: STORY GENERATION ===\n")
    print(story_system_prompt)
    print("\n\n\n")
    print(story_prompt)
    print("\n\n\n")
    # Generate story segment
    story_segment = stream_ollama(story_system_prompt, story_prompt)
    last_paragraph = get_last_paragraph(story_segment)
    
    with open("temp/allstory.txt","a") as finalstory:
        finalstory.write("\n" + story_segment)

    # Update summary using previous summary and new story segment
    summary_prompt = f"Previous Summary: {summary}\n\n\n\nNew Story Segment: {story_segment}\n\n\n\nUpdate the summary."

    print("\n\n\n\n\nUPDATING SUMMARY")
    print(summary_prompt)
    summary = stream_ollama(summary_system_prompt, summary_prompt)
    
    # Set the new story segment as prompt for next round
    story_user_prompt = story_segment
