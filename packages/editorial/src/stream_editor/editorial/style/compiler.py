import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from stream_editor.contracts.style import EditorialStylePolicyContract, StyleSignal
# Assuming research contracts exist. For compilation we can accept raw dicts for flexibility 
# or explicit research contracts. We'll use kwargs/dicts here.

class StylePolicyCompiler:
    def __init__(self, n_threshold_low: int = 5, n_threshold_high: int = 50):
        self.n_threshold_low = n_threshold_low
        self.n_threshold_high = n_threshold_high
        
    def _calculate_confidence_weight(self, n: int, base_confidence: float) -> float:
        """Deterministically scales down influence of low-N observations."""
        if n < self.n_threshold_low:
            return 0.0 # Ignore noise
        if n >= self.n_threshold_high:
            return base_confidence
            
        # Linear scale between low and high thresholds
        scale = (n - self.n_threshold_low) / (self.n_threshold_high - self.n_threshold_low)
        return base_confidence * scale

    def compile(self, profile: Dict[str, Any], findings: List[Dict[str, Any]], project_id: Optional[str] = None) -> EditorialStylePolicyContract:
        """
        Compiles a StyleProfile and approved findings into a StylePolicy.
        - profile: the StyleProfile dict
        - findings: approved textual research findings
        """
        signals = []
        
        # Example heuristic: map 'reaction_clips_avg_duration' to a M5 pacing signal
        metrics = profile.get("metrics", {})
        
        # 1. Reaction Context Retention
        n_reactions = metrics.get("reaction_count", 0)
        reaction_conf = metrics.get("reaction_confidence", 0.5)
        weight = self._calculate_confidence_weight(n_reactions, reaction_conf)
        
        if weight > 0.3:
            signals.append(StyleSignal(
                name="reaction_retention",
                stage="M5",
                direction="increase",
                strength=0.5 * weight,  # Base strength scaled by confidence
                confidence=weight,
                sample_size=n_reactions,
                source_profile_metric="reaction_count"
            ))
            
        # 2. Pacing / Cut density
        n_cuts = metrics.get("cut_count", 0)
        pacing_conf = metrics.get("pacing_confidence", 0.6)
        pacing_weight = self._calculate_confidence_weight(n_cuts, pacing_conf)
        if pacing_weight > 0.4:
            signals.append(StyleSignal(
                name="rapid_cut_affinity",
                stage="M5",
                direction="increase" if metrics.get("cuts_per_minute", 0) > 10 else "decrease",
                strength=0.4 * pacing_weight,
                confidence=pacing_weight,
                sample_size=n_cuts,
                source_profile_metric="cuts_per_minute"
            ))

        # 3. Effect density (derived from transformed source / effects)
        n_effects = metrics.get("effect_count", 0)
        n_transformed = metrics.get("transformed_source_count", 0)
        effect_conf = metrics.get("effect_confidence", 0.5)
        total_effect_n = n_effects + (n_transformed // 2) # Transformed is weaker evidence of explicit effects
        
        effect_weight = self._calculate_confidence_weight(total_effect_n, effect_conf)
        if effect_weight > 0.4:
            signals.append(StyleSignal(
                name="effect_density",
                stage="M8",
                direction="increase",
                strength=0.3 * effect_weight,
                confidence=effect_weight,
                sample_size=total_effect_n,
                source_profile_metric="effect_count"
            ))
            
        # In a fully fleshed out compiler, we would parse structured findings 
        # and maybe use AntigravityClient for text -> style signal normalization.
        
        return EditorialStylePolicyContract(
            id=str(uuid.uuid4()),
            name=f"Compiled Policy from {profile.get('name', 'Unknown')}",
            description="Deterministically compiled from EditDNA",
            status="active",
            source_reference_project_id=profile.get("reference_project_id"),
            source_style_profile_id=profile.get("id"),
            source_style_profile_version=profile.get("version", 1),
            policy_version=1,
            experimental=profile.get("experimental", False),
            signals=signals,
            created_at=datetime.utcnow(),
            created_by="StylePolicyCompiler"
        )
