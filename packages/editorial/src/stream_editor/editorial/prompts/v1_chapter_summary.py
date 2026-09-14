import json

PROMPT_ID = "chapter_summary"
PROMPT_VERSION = "v1"

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_topics": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["summary", "key_topics"]
}

def build_prompt(transcript: str, start_time: float, end_time: float, level: str) -> str:
    return f"""You are summarizing a section of a live stream. Level: {level}.
Time: {start_time:.1f} to {end_time:.1f}.
Return ONLY valid JSON matching the schema below. No markdown formatting or extra text.

Schema:
{json.dumps(OUTPUT_SCHEMA, indent=2)}

Transcript:
{transcript}
"""
