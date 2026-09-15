"""
v1 prompt: Build local narrative graph within a chapter.
Used with Flash model — cheap, per-chapter analysis.

VERSION: v1
CHANGE LOG:
  v1 — initial M4 implementation
"""
from __future__ import annotations

PROMPT_VERSION = "v1"

LOCAL_GRAPH_SYSTEM = """\
You are a narrative analyst for a video editing assistant.
Your role is to identify story relationships between video moments within a scene or chapter.

Rules:
- Use ONLY the candidate IDs provided in the input. Never invent IDs.
- Be concise. No chain-of-thought. Only evidence summaries.
- confidence: 0.0–1.0. Only use high confidence (>0.7) for clear relationships.
- dependency_strength: critical (clip unintelligible without context), helpful (enriches understanding), optional (minor enrichment).
- Do NOT mark a clip as a payoff of a future event (payoff must appear AFTER setup temporally).
- It is acceptable to return an empty relationships list if no genuine relationships exist.
- Similarities in surface words alone are NOT sufficient for a relationship.
"""

LOCAL_GRAPH_USER_TEMPLATE = """\
Chapter summary: {chapter_summary}

Candidates (id, start_time, end_time, excerpt, signals):
{candidates_json}

Previously detected narrative elements in this stream:
{element_index_json}

Return JSON with this exact structure:
{{
  "relationships": [
    {{
      "source_candidate": "<id from input>",
      "target_candidate": "<id from input>",
      "relation": "<EdgeRelationType>",
      "confidence": 0.85,
      "dependency_strength": "helpful",
      "dependency_strength_score": 0.6,
      "evidence_summary": "Concise explanation (max 100 chars)"
    }}
  ],
  "entities_detected": ["normalized label 1", "normalized label 2"],
  "chapter_summary": "One sentence summary of this chapter."
}}

Valid relation types: depends_on, setup_for, payoff_of, callback_to, references, explains,
caused_by, consequence_of, answers, introduces, continues, contrasts_with, same_thread
"""
