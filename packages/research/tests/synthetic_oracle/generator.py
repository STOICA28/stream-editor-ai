import uuid
from typing import List, Dict, Any
from stream_editor.contracts.effect_planning import EffectType, EffectTargetType

class SyntheticOracle:
    def __init__(self) -> None:
        self.source_duration = 3600.0  # 1 hour
        self.edit_duration = 0.0
        self.true_blocks: List[Dict[str, Any]] = []
        self.true_effects: List[Dict[str, Any]] = []
        
    def generate_scenario_1(self) -> Dict[str, Any]:
        """Generates the required scenario for M10 testing."""
        # 1. Retained Region: 0s -> 60s (normal speed)
        self.add_block(source_start=0.0, source_end=60.0, edit_start=0.0, edit_end=60.0, speed=1.0)
        
        # 3. Retained Region with 2x Speed: 120s -> 180s
        self.add_block(source_start=120.0, source_end=180.0, edit_start=60.0, edit_end=90.0, speed=2.0)
        self.add_effect(effect_type="speed_up", source_start=120.0, source_end=180.0, edit_start=60.0, edit_end=90.0, target="full_frame")
        
        # 5. Retained Region with Zoom: 240s -> 300s
        self.add_block(source_start=240.0, source_end=300.0, edit_start=90.0, edit_end=150.0, speed=1.0)
        self.add_effect(effect_type="zoom_face", source_start=240.0, source_end=300.0, edit_start=90.0, edit_end=150.0, scale=1.5, target="facecam")
        
        # 6. Grayscale effect: 300s -> 360s
        self.add_block(source_start=300.0, source_end=360.0, edit_start=150.0, edit_end=210.0, speed=1.0)
        self.add_effect(effect_type="grayscale", source_start=300.0, source_end=360.0, edit_start=150.0, edit_end=210.0, target="full_frame")
        
        # 7. Screen -> Face sequence (M10 requirement)
        self.add_block(source_start=360.0, source_end=420.0, edit_start=210.0, edit_end=270.0, speed=1.0)
        self.add_effect(effect_type="crop_focus", source_start=360.0, source_end=390.0, edit_start=210.0, edit_end=240.0, target="screen_region")
        self.add_effect(effect_type="zoom_face", source_start=390.0, source_end=420.0, edit_start=240.0, edit_end=270.0, target="facecam")
        
        # 8. 0.5x Speed (Slow motion)
        self.add_block(source_start=420.0, source_end=450.0, edit_start=270.0, edit_end=330.0, speed=0.5)
        self.add_effect(effect_type="slow_motion", source_start=420.0, source_end=450.0, edit_start=270.0, edit_end=330.0, target="full_frame")
        
        # 9. Freeze frame
        self.add_block(source_start=450.0, source_end=451.0, edit_start=330.0, edit_end=335.0, speed=0.0)
        self.add_effect(effect_type="freeze_frame", source_start=450.0, source_end=451.0, edit_start=330.0, edit_end=335.0, target="full_frame")
        
        self.edit_duration = 335.0

        return {
            "blocks": self.true_blocks,
            "effects": self.true_effects,
            "source_duration": self.source_duration,
            "edit_duration": self.edit_duration
        }

    def add_block(self, source_start: float, source_end: float, edit_start: float, edit_end: float, speed: float) -> None:
        self.true_blocks.append({
            "id": str(uuid.uuid4()),
            "run_id": "dummy-run-id",
            "source_start": source_start,
            "source_end": source_end,
            "edit_start": edit_start,
            "edit_end": edit_end,
            "speed_ratio": speed,
            "audio_confidence": 0.99,
            "transcript_confidence": 0.95,
            "visual_confidence": 0.98,
            "combined_confidence": 0.98,
            "method": "combined",
            "is_manual_override": False
        })
        
    def add_effect(self, effect_type: str, source_start: float, source_end: float, edit_start: float, edit_end: float, target: str, **kwargs: Any) -> None:
        self.true_effects.append({
            "id": str(uuid.uuid4()),
            "pair_id": "dummy-pair-id",
            "effect_type": effect_type,
            "target": target,
            "source_start": source_start,
            "source_end": source_end,
            "edit_start": edit_start,
            "edit_end": edit_end,
            "confidence": 0.95,
            "detection_method": "visual",
            "is_manual_override": False,
            "is_false_positive": False,
            **kwargs
        })
