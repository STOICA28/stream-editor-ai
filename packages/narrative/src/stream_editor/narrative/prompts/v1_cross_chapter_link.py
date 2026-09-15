"""
v1 prompt: Cross-chapter narrative linking.
Used with Pro model — expensive, only called with plausible retrieval candidates.

VERSION: v1
CHANGE LOG:
  v1 — initial M4 implementation
"""
from __future__ import annotations

PROMPT_VERSION = "v1"

CROSS_CHAPTER_SYSTEM = """\
You are a senior narrative analyst for a video editing assistant.
Your task is to determine whether specific pairs of video moments across different chapters
have genuine narrative relationships that would matter to an editor.

Rules:
- Use ONLY the candidate IDs provided. Never invent IDs.
- Surface word similarity is NOT enough — require semantic narrative connection.
- Verify temporal direction: payoff_of/callback_to/consequence_of sources must appear AFTER target.
- Be strict: false positives are costly. When in doubt, return no relationship.
- No chain-of-thought. Only concise evidence summaries.
- dependency_strength_score 0.0–1.0 (not just enum label).
"""

CROSS_CHAPTER_USER_TEMPLATE = """\
Evaluate the following candidate pairs for cross-chapter narrative relationships.

Known narrative elements in this stream:
{element_index_json}

Candidate pairs to evaluate:
{pairs_json}

Return JSON:
{{
  "relationships": [
    {{
      "source_candidate": "<id>",
      "target_candidate": "<id>",
      "relation": "<EdgeRelationType>",
      "confidence": 0.90,
      "dependency_strength": "critical",
      "dependency_strength_score": 0.85,
      "evidence_summary": "Concise explanation (max 150 chars)"
    }}
  ],
  "entities_detected": [],
  "chapter_summary": ""
}}

If no genuine relationship exists for a pair, omit it entirely from relationships.
Valid relation types: depends_on, setup_for, payoff_of, callback_to, references, explains,
caused_by, consequence_of, answers, introduces, continues, contrasts_with, same_thread
"""
