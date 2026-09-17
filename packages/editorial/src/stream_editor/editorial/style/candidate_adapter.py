from typing import List, Optional, Dict
from stream_editor.contracts.style import EditorialStylePolicyContract, StyledCandidateAssessment, StyleInfluence
from stream_editor.contracts.editorial import CandidateSegmentContract

class CandidateStyleAdapter:
    """
    Applies an EditorialStylePolicy to base CandidateSegments (M3) to produce
    StyledCandidateAssessments.
    """
    def __init__(self, policy: Optional[EditorialStylePolicyContract] = None):
        self.policy = policy
        
    def adapt(self, candidates: List[CandidateSegmentContract]) -> List[StyledCandidateAssessment]:
        assessments = []
        
        # If no policy, apply empty style influences
        if not self.policy or not self.policy.signals:
            for cs in candidates:
                base_scores = {
                    "score_humor": cs.score_humor or 0.0,
                    "score_reaction": cs.score_reaction or 0.0,
                    "score_story_value": cs.score_story_value or 0.0,
                }
                assessments.append(StyledCandidateAssessment(
                    candidate_id=cs.id,
                    base_scores=base_scores,
                    influences=[]
                ))
            return assessments
            
        m5_signals = [s for s in self.policy.signals if s.stage in ("M3", "M5")]
        
        for cs in candidates:
            base_scores = {
                "score_humor": cs.score_humor or 0.0,
                "score_reaction": cs.score_reaction or 0.0,
                "score_story_value": cs.score_story_value or 0.0,
            }
            
            influences = []
            candidate_duration = cs.duration
            
            for sig in m5_signals:
                if sig.name == "rapid_cut_affinity":
                    if candidate_duration < 3.0 and sig.direction == "increase":
                        influences.append(StyleInfluence(
                            candidate_id=cs.id,
                            dimension="pacing",
                            direction="increase",
                            strength=sig.strength * 1.5,
                            confidence=sig.confidence,
                            source_metric=sig.source_profile_metric,
                            evidence_count=sig.sample_size
                        ))
                    elif candidate_duration > 10.0 and sig.direction == "decrease":
                        influences.append(StyleInfluence(
                            candidate_id=cs.id,
                            dimension="pacing",
                            direction="decrease",
                            strength=sig.strength * 0.5,
                            confidence=sig.confidence,
                            source_metric=sig.source_profile_metric,
                            evidence_count=sig.sample_size
                        ))
                elif sig.name == "reaction_retention" and sig.direction == "increase":
                    if cs.score_reaction and cs.score_reaction > 0.5:
                        influences.append(StyleInfluence(
                            candidate_id=cs.id,
                            dimension="narrative_role",
                            direction="increase",
                            strength=sig.strength,
                            confidence=sig.confidence,
                            source_metric=sig.source_profile_metric,
                            evidence_count=sig.sample_size
                        ))
                            
            assessments.append(StyledCandidateAssessment(
                candidate_id=cs.id,
                base_scores=base_scores,
                influences=influences
            ))
            
        return assessments
