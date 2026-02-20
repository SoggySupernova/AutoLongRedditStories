import requests
import json
import os

# clear previous story
with open("temp/allstory.txt","w") as blank:
    blank.write("")

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
        "keep_alive": 1000
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

numrounds = 15

def get_last_paragraph(text):
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    return paragraphs[-1] if paragraphs else ""


# System prompt for story generation
story_system_prompt = """You are a long-form story generator.

**Response Formatting:**
Generate a coherent story segment of about 500 words.
Do NOT include the summary in the story.
Respond ONLY with the new segment of the story.
Do not repeat the previous part of the story in your response.
Never use any Markdown styling.


**Story Style**:
The story should be fiction but plausible—no creepy monsters, fantasy creatures, or impossible environments.
Do not stray too far from the original theme.
It should be in the first person perspective.
If the story begins to sound abstract, supernatural, or like science fiction, IMMEDIATELY course-correct by returning to concrete actions, dialogue, or physical investigation.

"""







hook_sentence = "My childhood home is for sale. The listing photos show a locked door I’ve never seen before."
theme_sentence = "The narrator sees their old childhood home from 20 years ago on sale, but the photos show a locked door that the narrator's never seen before."
more_detailed_theme_sentence = "The story starts with the narrator seeing their old childhood home from 20 years ago on sale, but the photos show a locked door that the narrator's never seen before. The narrator revisits the house and discovers a concealed room behind the basement shelving. Inside are detailed journals written by someone documenting the family’s routines. The entries stop abruptly the night the narrator moved out. They file a police report that results in an unexpected encounter with the writer of the journals who had been secretly living in their house ever since the family moved in."


plot_beats_prompt = f"""
You are a story structure engine.

Given a single theme sentence as input, generate exactly 15 sequential plot beats that expand the premise into a complete narrative arc.

Requirements:

* Each generated plot beat should be on its own line. Respond only with the generated plot beats and no commentary.
* Each beat must be 2–3 sentences.
* The story should not be abstract, supernatural, or science fiction. It should be plasible in real life.
* Maintain genre consistency implied by the premise.
* Ensure logical cause-and-effect progression between beats.
* Your goal is to create wide, consequential, story-shifting beats — not micro-actions, filler transitions, or repetitive exploration steps. Each beat should be its **own moment in time**.
* The final beat must close the arc rather than end ambiguously (unless ambiguity is inherent to the theme).
* **YOU SHOULD NOT BE WRITING A STORY, JUST A PLOT FOR A STORY.**

Now generate the 15 plot beats for the following input:
"""

def string_to_dict(multi_line_string):
    # Split into lines, remove empty/whitespace-only lines, strip each line
    lines = [line.strip() for line in multi_line_string.splitlines() if line.strip()]

    # Create dict with keys 1 to len(lines); assumes up to 15 non-empty lines
    result = {i+1: line for i, line in enumerate(lines[:15])}
    return result

plot_beats_string = stream_ollama(plot_beats_prompt, more_detailed_theme_sentence)
plot_beats = string_to_dict(plot_beats_string)
print(plot_beats)

"""
plot_beats = {
    1: "The narrator arrives at the childhood home, enters, and notices things feel off.",
    2: "The narrator explores the main floor, feeling nostalgic but uneasy.",
    3: "The narrator heads down to the basement and notices the shelving looks strange.",
    4: "The narrator discovers and opens the concealed room behind the basement shelving.",
    5: "The narrator enters the room and finds the detailed journals.",
    6: "The narrator reads the journals, realizing someone documented their family's daily routines.",
    7: "The narrator discovers the journal entries stop abruptly the exact night they moved out.",
    8: "Feeling panicked, the narrator leaves the house and files a police report.",
    9: "The police investigate but find nothing conclusive, telling the narrator to stay away.",
    10: "Unable to let it go, the narrator returns to the house at night to look for missed clues.",
    11: "While investigating the dark house, the narrator hears a deliberate noise upstairs.",
    12: "The unexpected encounter: The narrator comes face-to-face with the journal writer.",
    13: "The writer reveals they've been secretly living in the walls/house ever since the family moved in.",
    14: "A tense confrontation occurs as the narrator tries to escape the house.",
    15: "The narrator escapes as the police arrive. Wrap up the story and describe the aftermath."
}
"""



# System prompt for summary update
summary_system_prompt = f"""
You are a story summarizer. Using the existing summary and the new story segment, update the summary to approximately 100 words.

* If no prior summary exists, create a new one (~100 words).
* Pack as much information as possible into the word limit- do not waste space writing complete sentences.
* **MOST IMPORTANT**: Only add or modify information based on the new segment; **do not replace the summary with a recap of the new segment.**
* Remove information only if needed to keep the summary within length, and remove only nonessential details.
* Do not invent details beyond the provided text.
* Include specific names, objects, events, and unresolved plot threads.
* Focus on essential plot progression, character developments, and continuity-critical details.
* Also keep in mind the plot sentence: {theme_sentence}

Respond with the summary only. Do not add commentary or generate new story content.
"""

# Initial user prompt for story generation
story_user_prompt = ""
















# Initial empty summary
summary = "No summary yet."

first_beat = plot_beats.get(1, "")

# Different prompt for the first time works better with smaller models
story_prompt = f"""Round 1 of {numrounds}

Write the beginning of a new story based on the opener and plot.
Do not repeat the hook sentence in the story, but the beginning of the story should take place right after the hook sentence.

Hook sentence: {hook_sentence}
Overall Plot: {theme_sentence}
Your goal for this segment (do not write more than this): {first_beat}
"""



endingmessage = ""

last_paragraph = ""


for round_number in range(1, numrounds + 1):
    current_goal = plot_beats.get(round_number, "Continue advancing the story naturally.")
    next_goal = plot_beats.get(round_number + 1, "This is the end, never mind")

    if round_number > 1:
        story_prompt = f"""Round {round_number} of {numrounds}

Overall Plot (just a reminder): {theme_sentence}

Current Story Summary:
{summary}

Last paragraph of previous segment:
{last_paragraph}

**YOUR GOAL FOR THIS SEGMENT:**
{current_goal}

**INSTRUCTIONS:**
* Continue the story naturally from the last paragraph.
* Do not repeat the last paragraph.
* Focus strictly on achieving the GOAL FOR THIS SEGMENT.
* Do not write more than specified by the goal.
For reference, here is the goal for the NEXT round: {next_goal}
Do NOT write about topics that will be written in the next round.
* Write in the first-person perspective.
""" # indentation is weird



    print(f"=== ROUND {round_number}: STORY GENERATION ===\n\n--- SYSTEM PROMPT ---")
    print(story_system_prompt)
    print("\n\n\n--- USER PROMPT ---")
    print(story_prompt)
    print("\n\n\n-- RESPONSE ---")
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
