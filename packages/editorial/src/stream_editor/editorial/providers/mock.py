from stream_editor.contracts.editorial import (
    CandidateAnalysisResult,
    EditorialAnalysisProvider,
    LocalFeatures,
    ScoreComponents,
)


class MockEditorialProvider(EditorialAnalysisProvider):
    flash_model_name = "mock-flash"
    pro_model_name = "mock-pro"

    def analyze_candidate(
        self,
        candidate_id: str,
        transcript_excerpt: str,
        local_features: LocalFeatures,
        nearby_events: list[dict],  # type: ignore[type-arg]
        local_summary: str | None,
        chapter_summary: str | None,
        prompt_version: str
    ) -> CandidateAnalysisResult:
        text = transcript_excerpt.lower()
        
        if "funny" in text or "haha" in text:
            return CandidateAnalysisResult(
                summary="Funny moment detected.",
                signals=ScoreComponents(humor=0.8, reaction=0.7, chat_relevance=0.6, visual_interest=0.5, importance=0.4, novelty=0.5, emotional_intensity=0.6, story_value=0.5, repetition=0.0),
                confidence=0.9,
                reasoning_summary=["Contains laughter keywords."]
            )
            
        if "important" in text or "crucial" in text:
            return CandidateAnalysisResult(
                summary="Important story beat.",
                signals=ScoreComponents(importance=0.9, story_value=0.8, humor=0.1, reaction=0.2, visual_interest=0.5, chat_relevance=0.3, novelty=0.6, emotional_intensity=0.5, repetition=0.0),
                confidence=0.85,
                reasoning_summary=["Contains importance keywords."]
            )

        if len(text) < 10:
            return CandidateAnalysisResult(
                summary="Low signal segment.",
                signals=ScoreComponents(humor=0.1, reaction=0.1, importance=0.1, visual_interest=0.1, chat_relevance=0.1, novelty=0.1, emotional_intensity=0.1, story_value=0.1, repetition=0.1),
                confidence=0.2,
                reasoning_summary=["Too short to analyze."]
            )

        return CandidateAnalysisResult(
            summary="Ambiguous segment.",
            signals=ScoreComponents(humor=0.5, reaction=0.5, importance=0.5, visual_interest=0.5, chat_relevance=None, novelty=0.5, emotional_intensity=0.5, story_value=0.5, repetition=0.5),
            confidence=0.5,
            reasoning_summary=["No clear keywords found."]
        )

    def summarize_window(
        self,
        transcript: str,
        start_time: float,
        end_time: float,
        level: str,
        prompt_version: str
    ) -> dict:  # type: ignore[type-arg]
        return {
            "summary": "Mock summary",
            "key_topics": ["topic 1"]
        }
