"""
TranscriptWindowSummarizer: hierarchical transcript summarization.

Creates local (5-15min) and chapter-level summaries for efficient
context supply to the editorial analysis provider.

Summaries are stored in the TranscriptWindow table and keyed by
derivation_signature for idempotent re-use.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime

from stream_editor.contracts.editorial import EditorialAnalysisProvider
from stream_editor.editorial.prompts.v1_chapter_summary import PROMPT_VERSION


class TranscriptWindowSummarizer:
    """
    Builds hierarchical transcript window summaries.

    Levels:
    - local: 5-15 minute windows
    - chapter: groups of 2-3 local windows (30-45 min)
    """

    LOCAL_WINDOW_MINUTES: float = 10.0  # default local window duration
    CHAPTER_SIZE: int = 3               # local windows per chapter

    def summarize_asset(
        self,
        project_id: str,
        source_asset_id: str,
        transcript_run_id: str,
        segments: list[dict[str, object]],
        provider: EditorialAnalysisProvider,
        db: object,
    ) -> None:
        """
        Build local + chapter summaries for an entire asset.

        Args:
            segments: List of dicts with 'start_time', 'end_time', 'text'.
            provider: EditorialAnalysisProvider (mock or real).
            db: Synchronous SQLAlchemy session.
        """
        if not segments:
            return

        asset_duration = max(float(str(s.get("end_time", 0))) for s in segments)
        window_seconds = self.LOCAL_WINDOW_MINUTES * 60

        # Build local windows
        local_window_ids: list[str] = []
        t = 0.0
        while t < asset_duration:
            window_end = min(t + window_seconds, asset_duration)
            window_segs = [
                s for s in segments
                if float(str(s.get("end_time", 0))) > t
                and float(str(s.get("start_time", 0))) < window_end
            ]
            transcript_text = " ".join(str(s.get("text", "")) for s in window_segs)

            sig = self._signature(
                project_id, source_asset_id, transcript_run_id, t, window_end, "local"
            )
            window_id = self._get_or_create_window(
                db=db,
                project_id=project_id,
                source_asset_id=source_asset_id,
                transcript_run_id=transcript_run_id,
                start_time=t,
                end_time=window_end,
                level="local",
                parent_window_id=None,
                transcript_text=transcript_text,
                provider=provider,
                derivation_signature=sig,
            )
            local_window_ids.append(window_id)
            t = window_end

        # Build chapter windows (groups of CHAPTER_SIZE local windows)
        for i in range(0, len(local_window_ids), self.CHAPTER_SIZE):
            chapter_ids = local_window_ids[i : i + self.CHAPTER_SIZE]
            from stream_editor.api.models.project import TranscriptWindow as DBWindow
            db_windows = [
                db.query(DBWindow).filter(DBWindow.id == wid).first()  # type: ignore[attr-defined]
                for wid in chapter_ids
            ]
            db_windows = [w for w in db_windows if w is not None]
            if not db_windows:
                continue

            chapter_start = min(w.start_time for w in db_windows)
            chapter_end = max(w.end_time for w in db_windows)
            chapter_text = " ".join(w.summary or "" for w in db_windows)
            sig = self._signature(
                project_id, source_asset_id, transcript_run_id,
                chapter_start, chapter_end, "chapter"
            )
            # Use first local window as parent reference
            self._get_or_create_window(
                db=db,
                project_id=project_id,
                source_asset_id=source_asset_id,
                transcript_run_id=transcript_run_id,
                start_time=chapter_start,
                end_time=chapter_end,
                level="chapter",
                parent_window_id=chapter_ids[0],
                transcript_text=chapter_text,
                provider=provider,
                derivation_signature=sig,
            )

    def _get_or_create_window(
        self,
        *,
        db: object,
        project_id: str,
        source_asset_id: str,
        transcript_run_id: str,
        start_time: float,
        end_time: float,
        level: str,
        parent_window_id: str | None,
        transcript_text: str,
        provider: EditorialAnalysisProvider,
        derivation_signature: str,
    ) -> str:
        from stream_editor.api.models.project import TranscriptWindow as DBWindow

        existing = (
            db.query(DBWindow)  # type: ignore[attr-defined]
            .filter(DBWindow.derivation_signature == derivation_signature)
            .first()
        )
        if existing:
            return str(existing.id)

        result = provider.summarize_window(
            transcript=transcript_text,
            start_time=start_time,
            end_time=end_time,
            level=level,
            prompt_version=PROMPT_VERSION,
        )

        import uuid
        window = DBWindow(
            id=str(uuid.uuid4()),
            project_id=project_id,
            source_asset_id=source_asset_id,
            transcript_run_id=transcript_run_id,
            start_time=start_time,
            end_time=end_time,
            level=level,
            parent_window_id=parent_window_id,
            summary=str(result.get("summary", "")),
            key_topics=list(result.get("key_topics", [])),  # type: ignore[call-overload]
            provider="mock" if "MOCK" in str(result.get("summary", "")) else "gemini",
            prompt_version=PROMPT_VERSION,
            derivation_signature=derivation_signature,
            created_at=datetime.utcnow(),
        )
        db.add(window)  # type: ignore[attr-defined]
        db.commit()  # type: ignore[attr-defined]
        return str(window.id)

    def _signature(
        self,
        project_id: str,
        source_asset_id: str,
        transcript_run_id: str,
        start_time: float,
        end_time: float,
        level: str,
    ) -> str:
        data = {
            "project_id": project_id,
            "source_asset_id": source_asset_id,
            "transcript_run_id": transcript_run_id,
            "start_time": round(start_time, 3),
            "end_time": round(end_time, 3),
            "level": level,
            "prompt_version": PROMPT_VERSION,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
