from typing import Optional
from stream_editor.contracts.editorial import EditorialAnalysisProvider, CandidateAnalysisResult, ScoreComponents, LocalFeatures

class MockEditorialProvider:
    def analyze_candidate(
        self,
        *,
        candidate_id: str,
        transcript_excerpt: str,
        local_features: LocalFeatures,
        nearby_events: list[dict[str, object]],
        local_summary: Optional[str],
        chapter_summary: Optional[str],
        prompt_version: str,
    ) -> CandidateAnalysisResult:
        
        text = transcript_excerpt.lower() if transcript_excerpt else ""
        
        if not text or len(text.strip()) < 5:
            signals = ScoreComponents(
                humor=0.1, reaction=0.1, importance=0.1, visual_interest=0.1,
                chat_relevance=0.1, novelty=0.1, emotional_intensity=0.1,
                story_value=0.1, repetition=0.1
            )
            return CandidateAnalysisResult(
                summary="Low signal segment.",
                signals=signals,
                confidence=0.9,
                reasoning_summary=["Too short to analyze."],
                cache_hit=False
            )
            
        # check repetition logic by looking for same word repeated
        words = text.split()
        if len(words) >= 4 and len(set(words)) == 1:
            signals = ScoreComponents(
                humor=0.1, reaction=0.1, importance=0.1, visual_interest=0.1,
                chat_relevance=0.1, novelty=0.1, emotional_intensity=0.1,
                story_value=0.1, repetition=0.9
            )
            return CandidateAnalysisResult(
                summary="Highly repetitive segment.",
                signals=signals,
                confidence=0.8,
                reasoning_summary=["Words are repeated."],
                cache_hit=False
            )
            
        if "lol" in text or "haha" in text or "jaja" in text:
            signals = ScoreComponents(
                humor=0.9, reaction=0.8, importance=0.3, visual_interest=0.5,
                chat_relevance=0.5, novelty=0.5, emotional_intensity=0.7,
                story_value=0.3, repetition=0.1
            )
            return CandidateAnalysisResult(
                summary="Funny moment.",
                signals=signals,
                confidence=0.8,
                reasoning_summary=["Detected laughter keywords."],
                cache_hit=False
            )
            
        if "important" in text or "importante" in text:
            signals = ScoreComponents(
                humor=0.1, reaction=0.3, importance=0.9, visual_interest=0.5,
                chat_relevance=0.5, novelty=0.6, emotional_intensity=0.5,
                story_value=0.9, repetition=0.1
            )
            return CandidateAnalysisResult(
                summary="Important story beat.",
                signals=signals,
                confidence=0.85,
                reasoning_summary=["Detected importance keywords."],
                cache_hit=False
            )
            
        signals = ScoreComponents(
            humor=0.5, reaction=0.5, importance=0.5, visual_interest=0.5,
            chat_relevance=0.5, novelty=0.5, emotional_intensity=0.5,
            story_value=0.5, repetition=0.5
        )
        return CandidateAnalysisResult(
            summary="Ambiguous segment.",
            signals=signals,
            confidence=0.3,
            reasoning_summary=["No clear keywords found."],
            cache_hit=False
        )

    def summarize_window(
        self,
        *,
        transcript: str,
        start_time: float,
        end_time: float,
        level: str,
        prompt_version: str,
    ) -> dict[str, object]:
        return {
            "summary": "Deterministic window summary.",
            "key_topics": ["topic_a", "topic_b"]
        }
