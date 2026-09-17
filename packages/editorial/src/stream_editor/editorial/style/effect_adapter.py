from typing import List, Optional
from stream_editor.contracts.style import EditorialStylePolicyContract

class EffectStyleAdapter:
    """
    Applies an EditorialStylePolicy to effect selection (M8).
    This tells the pipeline what effects to prefer or avoid.
    """
    def __init__(self, policy: Optional[EditorialStylePolicyContract] = None):
        self.policy = policy
        
    def get_preferred_effects(self) -> List[str]:
        if not self.policy or not self.policy.signals:
            return []
            
        preferred = []
        for sig in self.policy.signals:
            if sig.stage == "M8" and sig.name == "effect_density" and sig.direction == "increase":
                # Basic mock logic for effect preferences based on policy
                preferred.append("zoom")
                preferred.append("sound_effect")
                
        return preferred

    def get_effect_density_modifier(self) -> float:
        if not self.policy or not self.policy.signals:
            return 1.0
            
        for sig in self.policy.signals:
            if sig.stage == "M8" and sig.name == "effect_density":
                if sig.direction == "increase":
                    return 1.0 + sig.strength
                elif sig.direction == "decrease":
                    return max(0.1, 1.0 - sig.strength)
        return 1.0
