"""Narrative Anchor Detector for StreamEditor AI.

Identifies and tags essential structural anchors (Stream Greeting, Game Start, Outro)
that must be preserved for narrative continuity regardless of excitement peaks or duration budgets.
"""

from typing import Sequence
from stream_editor.contracts.edit_plan import ClipPriority, EditClipContract


class NarrativeAnchorDetector:
    """Detects and protects structural anchors across a livestream timeline."""

    GREETING_WINDOW_SECONDS: float = 180.0
    GAME_START_WINDOW_START: float = 120.0
    GAME_START_WINDOW_END: float = 480.0

    @classmethod
    def tag_anchor_clips(
        cls,
        clips: Sequence[EditClipContract],
        total_source_duration: float | None = None
    ) -> list[EditClipContract]:
        """
        Analyzes a sequence of clips and returns a list with anchor metadata attached.
        Guarantees that opening greeting and game launch are designated as essential anchors.
        """
        if not clips:
            return []

        tagged_clips: list[EditClipContract] = []
        greeting_found = False
        game_start_found = False

        # Sort clips by source_start to evaluate chronological stream development
        sorted_clips = sorted(clips, key=lambda c: c.source_start)

        # 1. Identify STREAM_GREETING: The earliest clip within the opening window
        for clip in sorted_clips:
            clip_copy = clip.model_copy()

            # Check if this clip qualifies as STREAM_GREETING
            if not greeting_found and clip_copy.source_start <= cls.GREETING_WINDOW_SECONDS:
                clip_copy.is_narrative_anchor = True
                clip_copy.anchor_type = "STREAM_GREETING"
                clip_copy.priority = ClipPriority.essential
                greeting_found = True
                tagged_clips.append(clip_copy)
                continue

            # Check if this clip qualifies as GAME_START
            if not game_start_found and cls.GAME_START_WINDOW_START <= clip_copy.source_start <= cls.GAME_START_WINDOW_END:
                clip_copy.is_narrative_anchor = True
                clip_copy.anchor_type = "GAME_START"
                clip_copy.priority = ClipPriority.essential
                game_start_found = True
                tagged_clips.append(clip_copy)
                continue

            # Check if this clip qualifies as OUTRO (near the end of a long stream)
            if total_source_duration and total_source_duration > 600.0:
                if clip_copy.source_start >= (total_source_duration - 300.0):
                    clip_copy.is_narrative_anchor = True
                    clip_copy.anchor_type = "OUTRO"
                    clip_copy.priority = ClipPriority.essential
                    tagged_clips.append(clip_copy)
                    continue

            tagged_clips.append(clip_copy)

        return tagged_clips
