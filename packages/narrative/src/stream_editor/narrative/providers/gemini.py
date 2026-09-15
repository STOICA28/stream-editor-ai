"""
GeminiNarrativeProvider — Gemini-backed narrative reasoning.

Model routing:
  Flash → build_local_graph (cheap, per-chapter)
  Pro   → link_story_elements (expensive, cross-chapter plausible pairs only)
  Pro   → review_graph (selective critic pass)

Responses are validated against LocalGraphProposal before returning.
No Gemini-specific structures leak into the domain model.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

from stream_editor.contracts.editorial import (
    LocalGraphProposal,
    ProposedRelationship,
    StoryGraphConfig,
)
from stream_editor.narrative.prompts import v1_cross_chapter_link, v1_critic, v1_local_graph

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai  # type: ignore[import]
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False
    logger.warning("google-generativeai not installed — GeminiNarrativeProvider unavailable")


def _make_cache_key(model: str, prompt_version: str, content: str) -> str:
    payload = json.dumps({"model": model, "prompt_version": prompt_version, "content": content}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


class GeminiNarrativeProvider:
    """
    Gemini-backed narrative reasoning provider.

    Uses Flash for local chapter analysis (cheap/fast).
    Uses Pro for cross-chapter linking and critic (expensive/accurate).
    """

    def __init__(self, api_key: str | None = None) -> None:
        if not _GENAI_AVAILABLE:
            raise RuntimeError(
                "google-generativeai package is required for GeminiNarrativeProvider. "
                "Install it with: uv add google-generativeai"
            )
        if api_key:
            genai.configure(api_key=api_key)
        self._call_log: list[dict[str, Any]] = []

    def build_local_graph(
        self,
        chapter_candidates: list[dict[str, object]],
        chapter_summary: str,
        element_index: list[dict[str, object]],
        config: StoryGraphConfig,
    ) -> LocalGraphProposal:
        """Flash model — cheap local chapter analysis."""
        candidates_json = json.dumps(
            [
                {
                    "id": c.get("id"),
                    "start_time": c.get("start_time"),
                    "end_time": c.get("end_time"),
                    "excerpt": (str(c.get("transcript_excerpt", "") or ""))[:300],
                    "summary": (str(c.get("summary", "") or ""))[:200],
                    "signals": c.get("source_signals", []),
                }
                for c in chapter_candidates
            ],
            indent=2,
        )
        element_index_json = json.dumps(element_index[:20], indent=2)

        user_prompt = v1_local_graph.LOCAL_GRAPH_USER_TEMPLATE.format(
            chapter_summary=chapter_summary,
            candidates_json=candidates_json,
            element_index_json=element_index_json,
        )

        raw = self._call_model(
            model=config.flash_model,
            system=v1_local_graph.LOCAL_GRAPH_SYSTEM,
            user=user_prompt,
            prompt_version=v1_local_graph.PROMPT_VERSION,
        )
        return self._parse_proposal(raw, config.prompt_version)

    def link_story_elements(
        self,
        candidate_pairs: list[tuple[dict[str, object], dict[str, object]]],
        element_index: list[dict[str, object]],
        config: StoryGraphConfig,
    ) -> LocalGraphProposal:
        """Pro model — evaluate plausible cross-chapter pairs from retrieval."""
        pairs_json = json.dumps(
            [
                {
                    "source": {
                        "id": s.get("id"),
                        "start_time": s.get("start_time"),
                        "excerpt": (str(s.get("transcript_excerpt", "") or ""))[:300],
                        "summary": (str(s.get("summary", "") or ""))[:200],
                    },
                    "target": {
                        "id": t.get("id"),
                        "start_time": t.get("start_time"),
                        "excerpt": (str(t.get("transcript_excerpt", "") or ""))[:300],
                        "summary": (str(t.get("summary", "") or ""))[:200],
                    },
                }
                for s, t in candidate_pairs
            ],
            indent=2,
        )
        element_index_json = json.dumps(element_index[:30], indent=2)

        user_prompt = v1_cross_chapter_link.CROSS_CHAPTER_USER_TEMPLATE.format(
            element_index_json=element_index_json,
            pairs_json=pairs_json,
        )

        raw = self._call_model(
            model=config.pro_model,
            system=v1_cross_chapter_link.CROSS_CHAPTER_SYSTEM,
            user=user_prompt,
            prompt_version=v1_cross_chapter_link.PROMPT_VERSION,
        )
        return self._parse_proposal(raw, config.prompt_version)

    def review_graph(
        self,
        nodes: list[dict[str, object]],
        edges: list[dict[str, object]],
        threads: list[dict[str, object]],
        config: StoryGraphConfig,
    ) -> list[ProposedRelationship]:
        """Pro model — critic pass on assembled graph."""
        nodes_json = json.dumps(nodes[:50], indent=2)
        edges_json = json.dumps(edges[:100], indent=2)
        threads_json = json.dumps(threads[:20], indent=2)

        user_prompt = v1_critic.CRITIC_USER_TEMPLATE.format(
            nodes_json=nodes_json,
            edges_json=edges_json,
            threads_json=threads_json,
        )

        raw = self._call_model(
            model=config.pro_model,
            system=v1_critic.CRITIC_SYSTEM,
            user=user_prompt,
            prompt_version=v1_critic.PROMPT_VERSION,
        )
        proposal = self._parse_proposal(raw, config.prompt_version)
        return proposal.relationships

    def get_call_log(self) -> list[dict[str, Any]]:
        """Return cost telemetry log."""
        return list(self._call_log)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _call_model(
        self,
        model: str,
        system: str,
        user: str,
        prompt_version: str,
    ) -> str:
        start_ms = int(time.time() * 1000)
        try:
            m = genai.GenerativeModel(
                model_name=model,
                system_instruction=system,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            resp = m.generate_content(user)
            text = resp.text
            usage = getattr(resp, "usage_metadata", None)
            self._call_log.append({
                "model": model,
                "prompt_version": prompt_version,
                "input_tokens": getattr(usage, "prompt_token_count", None),
                "output_tokens": getattr(usage, "candidates_token_count", None),
                "latency_ms": int(time.time() * 1000) - start_ms,
            })
            return text
        except Exception as exc:
            logger.error("Gemini API error for model %s: %s", model, exc)
            self._call_log.append({
                "model": model,
                "prompt_version": prompt_version,
                "error": str(exc),
                "latency_ms": int(time.time() * 1000) - start_ms,
            })
            return "{}"

    def _parse_proposal(self, raw: str, prompt_version: str) -> LocalGraphProposal:
        """Parse and validate model JSON output into a LocalGraphProposal."""
        try:
            data = json.loads(raw)
            return LocalGraphProposal.model_validate(data)
        except Exception as exc:
            logger.warning("Failed to parse model output as LocalGraphProposal: %s\nRaw: %s", exc, raw[:500])
            return LocalGraphProposal(prompt_version=prompt_version)
