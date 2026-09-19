import json
import asyncio
import logging
from typing import Any

from stream_editor.contracts.editorial import (
    LocalGraphProposal,
    ProposedRelationship,
    StoryGraphConfig,
)
from stream_editor.narrative.prompts import v1_cross_chapter_link, v1_critic, v1_local_graph
from stream_editor.models.antigravity_client import AntigravityClient, AIProviderUnavailable

logger = logging.getLogger(__name__)

class AntigravityNarrativeProvider:
    def __init__(self, client: AntigravityClient):
        self.client = client
        self._call_log: list[dict[str, Any]] = []

    def build_local_graph(
        self,
        chapter_candidates: list[dict[str, object]],
        chapter_summary: str,
        element_index: list[dict[str, object]],
        config: StoryGraphConfig,
    ) -> LocalGraphProposal:
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
        
        prompt = (
            "Analyze only the provided evidence.\n"
            "Return the required structured output.\n"
            "Do not modify repository files.\n"
            "Do not execute commands.\n"
            "Do not invoke tools.\n"
            "Do not change project state.\n\n"
            + v1_local_graph.LOCAL_GRAPH_SYSTEM + "\n\n" + user_prompt
        )

        try:
            return asyncio.run(self.client.generate_structured(prompt, LocalGraphProposal))
        except AIProviderUnavailable as e:
            logger.warning(f"Antigravity unavailable: {e}")
            return LocalGraphProposal(prompt_version=config.prompt_version)
        except Exception as e:
            logger.error(f"Failed to generate local graph: {e}")
            return LocalGraphProposal(prompt_version=config.prompt_version)

    def link_story_elements(
        self,
        candidate_pairs: list[tuple[dict[str, object], dict[str, object]]],
        element_index: list[dict[str, object]],
        config: StoryGraphConfig,
    ) -> LocalGraphProposal:
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

        prompt = (
            "Analyze only the provided evidence.\n"
            "Return the required structured output.\n"
            "Do not modify repository files.\n"
            "Do not execute commands.\n"
            "Do not invoke tools.\n"
            "Do not change project state.\n\n"
            + v1_cross_chapter_link.CROSS_CHAPTER_SYSTEM + "\n\n" + user_prompt
        )

        try:
            return asyncio.run(self.client.generate_structured(prompt, LocalGraphProposal))
        except Exception as e:
            logger.error(f"Failed to link story elements: {e}")
            return LocalGraphProposal(prompt_version=config.prompt_version)

    def review_graph(
        self,
        nodes: list[dict[str, object]],
        edges: list[dict[str, object]],
        threads: list[dict[str, object]],
        config: StoryGraphConfig,
    ) -> list[ProposedRelationship]:
        nodes_json = json.dumps(nodes[:50], indent=2)
        edges_json = json.dumps(edges[:100], indent=2)
        threads_json = json.dumps(threads[:20], indent=2)

        user_prompt = v1_critic.CRITIC_USER_TEMPLATE.format(
            nodes_json=nodes_json,
            edges_json=edges_json,
            threads_json=threads_json,
        )

        prompt = (
            "Analyze only the provided evidence.\n"
            "Return the required structured output.\n"
            "Do not modify repository files.\n"
            "Do not execute commands.\n"
            "Do not invoke tools.\n"
            "Do not change project state.\n\n"
            + v1_critic.CRITIC_SYSTEM + "\n\n" + user_prompt
        )
        
        try:
            proposal: LocalGraphProposal = asyncio.run(
                self.client.generate_structured(prompt, LocalGraphProposal)
            )
            return proposal.relationships
        except Exception as e:
            logger.error(f"Failed to review graph: {e}")
            return []

    def get_call_log(self) -> list[dict[str, Any]]:
        return list(self._call_log)
