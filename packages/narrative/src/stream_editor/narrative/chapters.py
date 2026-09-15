"""
ChapterGrouper — groups candidate segments into bounded narrative chapters.

Priority:
1. TranscriptWindow chapter boundaries from M3 (if available)
2. Temporal fallback: fixed-duration windows

Chapter grouping is cheap and deterministic — no model calls.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Chapter:
    index: int
    start_time: float
    end_time: float
    source: str  # "transcript_window" | "temporal_fallback"
    candidates: list[dict[str, object]] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class ChapterGrouper:
    """
    Groups candidate dicts into chapters for bounded local processing.

    Each chapter contains candidates whose start_time falls within [chapter_start, chapter_end).
    A candidate always belongs to exactly one chapter.
    """

    def __init__(self, chapter_duration_seconds: float = 600.0) -> None:
        self._chapter_duration = chapter_duration_seconds

    def group(
        self,
        candidates: list[dict[str, object]],
        transcript_windows: list[dict[str, object]] | None = None,
    ) -> list[Chapter]:
        """
        Group candidates into chapters.

        Args:
            candidates: List of candidate dicts with 'start_time', 'end_time', 'id' keys.
            transcript_windows: Optional list of chapter-level TranscriptWindow dicts
                                 with 'start_time', 'end_time', 'level' keys.

        Returns:
            Ordered list of Chapter objects. Empty candidates produce no chapter.
        """
        if not candidates:
            return []

        # Sort by start_time
        sorted_candidates = sorted(candidates, key=lambda c: float(str(c.get("start_time", 0))))

        # Attempt to use transcript windows (level == "chapter")
        chapter_windows: list[dict[str, object]] = []
        if transcript_windows:
            chapter_windows = [
                w for w in transcript_windows
                if str(w.get("level", "")) == "chapter"
            ]
            chapter_windows.sort(key=lambda w: float(str(w.get("start_time", 0))))

        if chapter_windows:
            return self._group_by_windows(sorted_candidates, chapter_windows)
        else:
            return self._group_by_duration(sorted_candidates)

    def _group_by_windows(
        self,
        candidates: list[dict[str, object]],
        windows: list[dict[str, object]],
    ) -> list[Chapter]:
        chapters: list[Chapter] = []
        for idx, window in enumerate(windows):
            w_start = float(str(window.get("start_time", 0)))
            w_end = float(str(window.get("end_time", 0)))
            chapter = Chapter(
                index=idx,
                start_time=w_start,
                end_time=w_end,
                source="transcript_window",
            )
            for c in candidates:
                c_start = float(str(c.get("start_time", 0)))
                if w_start <= c_start < w_end:
                    chapter.candidates.append(c)
            if chapter.candidates:
                chapters.append(chapter)
        # Any candidates after last window go into final chapter
        if windows:
            last_end = float(str(windows[-1].get("end_time", 0)))
            stragglers = [
                c for c in candidates
                if float(str(c.get("start_time", 0))) >= last_end
            ]
            if stragglers:
                extra = Chapter(
                    index=len(chapters),
                    start_time=last_end,
                    end_time=float(str(stragglers[-1].get("end_time", last_end))),
                    source="transcript_window",
                    candidates=stragglers,
                )
                chapters.append(extra)
        logger.info("Grouped %d candidates into %d chapters (transcript_window)", len(candidates), len(chapters))
        return chapters

    def _group_by_duration(
        self,
        candidates: list[dict[str, object]],
    ) -> list[Chapter]:
        if not candidates:
            return []
        stream_start = float(str(candidates[0].get("start_time", 0)))
        stream_end = float(str(candidates[-1].get("end_time", stream_start)))

        chapters: list[Chapter] = []
        chapter_start = stream_start
        chapter_index = 0

        while chapter_start <= stream_end:
            chapter_end = chapter_start + self._chapter_duration
            chapter = Chapter(
                index=chapter_index,
                start_time=chapter_start,
                end_time=chapter_end,
                source="temporal_fallback",
            )
            for c in candidates:
                c_start = float(str(c.get("start_time", 0)))
                if chapter_start <= c_start < chapter_end:
                    chapter.candidates.append(c)
            if chapter.candidates:
                chapters.append(chapter)
            chapter_start = chapter_end
            chapter_index += 1

        logger.info(
            "Grouped %d candidates into %d chapters (temporal_fallback, duration=%.0fs)",
            len(candidates), len(chapters), self._chapter_duration,
        )
        return chapters
