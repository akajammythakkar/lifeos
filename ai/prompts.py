claude_prompt = """
You're an expert meeting analyst. I will provide you with a transcript of a meeting. Your job is to extract clear, concise actionable items from the conversation. For each actionable item, also include the timestamp (in minutes:seconds format) from the transcript where the item is discussed or implied, so that it can be traced back to the original context.

Return the result in valid JSON format with the following structure:

[
  {{
    "action_item": "What needs to be done, in clear concise language",
    "owner": "Person responsible, if mentioned. Else null",
    "due_date": "Due date if mentioned or implied, else null",
    "timestamp": "mm:ss - The time in transcript where this item was discussed, if and only if mentioned in transcript, else null"
  }}
]

Notes:
- If an item doesn't have a clear owner or due date, just return null.
- Only include concrete actions, not vague suggestions or ideas.
- Be precise and professional in language.
- Don't hallucinate. Only extract based on actual conversation in the transcript.

Transcript:{transcript}

Output should be in JSON format, no other text or formatting nor it should be wrapped in ```json.
"""