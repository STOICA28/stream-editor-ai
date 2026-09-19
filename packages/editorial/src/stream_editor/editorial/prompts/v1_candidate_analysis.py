import json

PROMPT_ID = "candidate_analysis"
PROMPT_VERSION = "v1"

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "signals": {
            "type": "object",
            "properties": {
                "humor": {"type": ["number", "null"]},
                "reaction": {"type": ["number", "null"]},
                "importance": {"type": ["number", "null"]},
                "visual_interest": {"type": ["number", "null"]},
                "chat_relevance": {"type": ["number", "null"]},
                "novelty": {"type": ["number", "null"]},
                "emotional_intensity": {"type": ["number", "null"]},
                "story_value": {"type": ["number", "null"]},
                "repetition": {"type": ["number", "null"]}
            }
        },
        "confidence": {"type": "number"},
        "reasoning_summary": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["summary", "signals", "confidence", "reasoning_summary"]
}

def build_prompt(transcript_excerpt: str, local_features: dict, nearby_events: list[dict], local_summary: str | None, chapter_summary: str | None) -> str:  # type: ignore[type-arg]
    return f"""You are an editorial assistant analyzing a live stream segment to determine if it is an interesting highlight.
Return ONLY valid JSON matching the following schema. Do NOT include markdown code blocks or chain-of-thought text.

Schema:
{json.dumps(OUTPUT_SCHEMA, indent=2)}

Context:
- Chapter Summary: {chapter_summary or "None"}
- Local Context Summary: {local_summary or "None"}

Segment details:
- Transcript: {transcript_excerpt}
- Local Features: {json.dumps(local_features)}
- Nearby Events: {json.dumps(nearby_events)}

Evaluate the segment and provide the required scores (0.0 to 1.0, or null if unknown), summary, confidence, and concise reasoning.
"""
