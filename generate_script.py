import requests
import json



numrounds = 3



# System prompt for story generation
story_system_prompt = """
You are a long-form story generator. 
Generate a coherent story segment of about 200 tokens.
Do NOT include the summary in the story.
Respond ONLY with the story continuation.
"""

# System prompt for summary update
summary_system_prompt = """
You are a story summarizer. 
Based on the previous summary and the new story segment, update the summary to about 400 words.
If there is no previous summary, just create a summary about 200 words.
The summary should include specific names, objects, and ideas, not general feelings, etc. The goal is to keep a separate story generator model from forgetting important details and losing continuity.
Include only essential story details, character developments, plot progression, and unresolved threads.
VERY IMPORTANT: DO NOT REPLACE IT WITH A SUMMARY OF THE NEW SEGMENT. ADD OR UPDATE INFORMATION. ONLY REMOVE INFORMATION IF THE SUMMARY GETS TOO LARGE. IF SO, ONLY REMOVE UNNECCESSARY INFORMATION.
Respond ONLY with the summary.
"""

# Initial user prompt for story generation
story_user_prompt = ""
theme_sentence = """
Opener: “My landlord texted, ‘Whatever you hear from apartment 3B tomorrow, you didn’t hear it.’”
Plot: Strange sounds begin exactly at midnight, and the narrator uncovers a pattern tied to former tenants who all moved out within a week.
"""

# Initial empty summary
summary = ""

# Ollama API settings
url = "http://localhost:11434/api/chat"
options = {"num_gpu": -1, "num_ctx": 65536}
model_name = "ministral-3:8b-instruct-2512-q4_K_M"

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
        "keep_alive": 0
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
    print("\n")  # separate each stream visually
    return result



for round_number in range(1, numrounds + 1):
    print(f"=== ROUND {round_number}: STORY GENERATION ===\n")
    story_prompt = f"Round {round_number} of {numrounds}\n\nGuidelines: {theme_sentence}\n\nSummary of prior events: {summary}\n\n\nPrevious story segment:\n\n\n{story_user_prompt}\n\n\nContinue the story or begin one based on the guidelines if there is no context. If creating a new story based on the guidelines, start before the beginning. Write about events that led up to this, etc. Let the theme develop over the {numrounds} rounds instead of jumping to the end right away. Do not use any Markdown styling. NEVER use an em dash. Use a comma, colon, or semicolon instead."
    print(story_prompt)
    print("\n\n\n")
    # Generate story segment
    story_segment = stream_ollama(story_system_prompt, story_prompt)
    
    with open("temp/allstory.txt","a") as finalstory:
        finalstory.write("\n" + story_segment)

    # Update summary using previous summary and new story segment
    summary_prompt = f"Previous Summary: {summary}\n\n\n\nNew Story Segment: {story_segment}\n\n\n\nUpdate the summary."
    print(summary_prompt)
    summary = stream_ollama(summary_system_prompt, summary_prompt)
    
    # Set the new story segment as prompt for next round
    story_user_prompt = story_segment
