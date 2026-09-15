import hashlib
import json
import logging
from typing import Optional
from stream_editor.contracts.rendering import CompiledSegment, RenderConfig

logger = logging.getLogger(__name__)

class RenderSegmentCache:
    def __init__(self, renderer_version: str = "1.0") -> None:
        self.renderer_version = renderer_version

    def compute_signature(
        self,
        source_fingerprint: str,
        segment: CompiledSegment,
        config: RenderConfig
    ) -> str:
        """
        Computes a deterministic hash for a render segment based on:
        source fingerprint + source range + effects + RenderConfig + renderer version.
        """
        data = {
            "source": source_fingerprint,
            "source_start": segment.source_start,
            "source_end": segment.source_end,
            "config": config.model_dump(mode="json"),
            "renderer_version": self.renderer_version,
            "effects": []
        }
        
        # Ensure effects are sorted deterministically so identical effects produce the same hash
        sorted_effects = sorted(segment.effects, key=lambda e: (e.effect_type.value, e.source_start))
        
        for eff in sorted_effects:
            eff_data = {
                "type": eff.effect_type.value,
                "start": eff.source_start,
                "end": eff.source_end,
                "parameters": eff.parameters
            }
            if eff.target_box:
                eff_data["box"] = eff.target_box.model_dump(mode="json")
            effects_list = data["effects"]
            if isinstance(effects_list, list):
                effects_list.append(eff_data)
            
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
