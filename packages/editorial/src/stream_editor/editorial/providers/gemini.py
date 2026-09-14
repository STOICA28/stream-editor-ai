import os
import time
import json
from typing import Optional
from stream_editor.contracts.editorial import EditorialAnalysisProvider, CandidateAnalysisResult, ScoreComponents, LocalFeatures
from stream_editor.editorial.prompts.v1_candidate_analysis import build_prompt as build_candidate_prompt
from stream_editor.editorial.prompts.v1_chapter_summary import build_prompt as build_chapter_prompt

try:
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted
except ImportError:
    genai = None

class GeminiEditorialProvider:
    def __init__(self):
        if not genai:
            raise RuntimeError("google.generativeai is not installed")
            
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not configured")
            
        genai.configure(api_key=api_key)
        
        self.flash_model_name = os.environ.get("GEMINI_MODEL_FLASH", "gemini-2.0-flash")
        self.pro_model_name = os.environ.get("GEMINI_MODEL_PRO", "gemini-1.5-pro")

    def _call_with_retry(self, model_name: str, prompt: str) -> tuple[dict, dict]:
        model = genai.GenerativeModel(model_name)
        
        max_retries = 3
        delay = 1.0
        
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                    )
                )
                latency_ms = int((time.time() - start_time) * 1000)
                
                try:
                    data = json.loads(response.text)
                except json.JSONDecodeError:
                    raise RuntimeError("Failed to parse JSON response from model")
                    
                usage = getattr(response, 'usage_metadata', None)
                metadata = {
                    "input_tokens": usage.prompt_token_count if usage else None,
                    "output_tokens": usage.candidates_token_count if usage else None,
                    "latency_ms": latency_ms
                }
                
                return data, metadata
                
            except ResourceExhausted:
                if attempt == max_retries - 1:
                    raise
                time.sleep(delay)
                delay *= 2
            except Exception as e:
                raise RuntimeError(f"Gemini API error: {e}")
                
        raise RuntimeError("Max retries exceeded")

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
        
        prompt = build_candidate_prompt(
            transcript_excerpt=transcript_excerpt,
            local_features=local_features.to_dict(),
            nearby_events=nearby_events,
            local_summary=local_summary,
            chapter_summary=chapter_summary
        )
        
        data, metadata = self._call_with_retry(self.flash_model_name, prompt)
        
        signals_data = data.get("signals", {})
        signals = ScoreComponents(**signals_data)
        
        return CandidateAnalysisResult(
            summary=data.get("summary", ""),
            signals=signals,
            confidence=data.get("confidence", 0.0),
            reasoning_summary=data.get("reasoning_summary", []),
            input_tokens=metadata["input_tokens"],
            output_tokens=metadata["output_tokens"],
            latency_ms=metadata["latency_ms"],
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
        prompt = build_chapter_prompt(
            transcript=transcript,
            start_time=start_time,
            end_time=end_time,
            level=level
        )
        
        data, _ = self._call_with_retry(self.flash_model_name, prompt)
        return data
