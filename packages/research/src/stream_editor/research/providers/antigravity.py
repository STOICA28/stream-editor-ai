import os
import json
import uuid
import subprocess
import shutil
import hashlib
from typing import List, Dict, Any, Optional

from stream_editor.contracts.research import (
    AlignmentBlockContract,
    ObservedEffectContract,
    ObservedEditorialDecisionContract,
    EditorialDecisionType
)
from stream_editor.contracts.effect_planning import EffectType, EffectTargetType
from stream_editor.research.alignment.builder import MultiSignalAlignmentBuilder
from stream_editor.research.observation.detector import LocalEffectDetector
from pydantic import BaseModel, ValidationError

class AntigravityOutputSchema(BaseModel):
    classification: str
    confidence: float
    effect_type: Optional[str] = None
    target: Optional[str] = None

class AntigravityReferenceProvider:
    """
    Real Reference Provider that integrates local alignment, local effect detection,
    and selectively calls Antigravity (agy CLI) for semantic understanding and 
    ambiguous event classification using an existing authenticated session.
    """
    def __init__(self, flash_model: str = "gemini-1.5-flash-latest", pro_model: str = "gemini-1.5-pro-latest"):
        self.builder = MultiSignalAlignmentBuilder()
        self.detector = LocalEffectDetector()
        
        self.flash_model = flash_model
        self.pro_model = pro_model
        
        self.telemetry = {
            "provider": "antigravity",
            "local_windows": 0,
            "flash_calls": 0,
            "pro_calls": 0,
            "duration": 0.0,
            "tokens": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "failures": 0,
            "escalations": 0
        }
        
        # In-memory simple cache for demonstration. 
        # Cache signature: provider + model + schema + prompt + evidence
        self._cache = {}
        
        self.is_available = self._check_availability()
        
    def _check_availability(self) -> bool:
        agy_path = shutil.which("agy")
        if not agy_path:
            return False
        
        try:
            result = subprocess.run(
                ["agy", "-p", "Reply with OK", "--output-format", "json"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10
            )
            if result.returncode != 0:
                return False
            # Check if JSON is returned
            json.loads(result.stdout)
            return True
        except Exception:
            return False

    def _generate_cache_key(self, model: str, schema: str, prompt: str) -> str:
        signature = f"antigravity|{model}|{schema}|{prompt}"
        return hashlib.sha256(signature.encode('utf-8')).hexdigest()

    def _call_agy(self, prompt: str, model: str, schema_dict: Dict) -> Optional[AntigravityOutputSchema]:
        if not self.is_available:
            self.telemetry["failures"] += 1
            return None
            
        schema_str = json.dumps(schema_dict)
        cache_key = self._generate_cache_key(model, schema_str, prompt)
        
        if cache_key in self._cache:
            self.telemetry["cache_hits"] += 1
            return self._cache[cache_key]
            
        self.telemetry["cache_misses"] += 1
        
        try:
            result = subprocess.run(
                ["agy", "-p", prompt, "--output-format", "json", "--json-schema", schema_str, "--model", model],
                capture_output=True,
                text=True,
                check=False,
                timeout=30
            )
            
            if result.returncode != 0:
                self.telemetry["failures"] += 1
                return None
                
            try:
                data = json.loads(result.stdout)
                structured_output = data.get("structured_output", data)
                parsed = AntigravityOutputSchema.model_validate(structured_output)
                
                # Mock token counting based on output structure since agy format might vary
                self.telemetry["tokens"] += len(result.stdout) // 4 
                
                self._cache[cache_key] = parsed
                return parsed
                
            except (json.JSONDecodeError, ValidationError):
                self.telemetry["failures"] += 1
                return None
                
        except Exception:
            self.telemetry["failures"] += 1
            return None

    def align_media(self, source_path: str, edited_path: str) -> List[AlignmentBlockContract]:
        blocks = self.builder.build(source_path, edited_path)
        self.telemetry["local_windows"] += len(blocks)
        return blocks

    def detect_effects(self, alignment_blocks: List[AlignmentBlockContract], source_path: str, edited_path: str) -> List[ObservedEffectContract]:
        # 1. Local deterministic effects
        effects = self.detector.detect(alignment_blocks, source_path, edited_path)
        
        # 2. Freeze frames
        for i in range(len(alignment_blocks) - 1):
            b1 = alignment_blocks[i]
            b2 = alignment_blocks[i+1]
            e_gap = b2.edit_start - b1.edit_end
            s_gap = b2.source_start - b1.source_end
            if e_gap > 0.5 and s_gap < 0.2:
                effects.append(ObservedEffectContract(
                    id=str(uuid.uuid4()), pair_id="pair", effect_type=EffectType.FREEZE_FRAME, target=EffectTargetType.FULL_FRAME,
                    source_start=b1.source_end, source_end=b2.source_start, edit_start=b1.edit_end, edit_end=b2.edit_start,
                    confidence=0.9, detection_method="alignment", is_manual_override=False, is_false_positive=False
                ))
        
        # 3. Escalate ambiguous effects to Antigravity
        schema_dict = AntigravityOutputSchema.model_json_schema()
        
        for b in alignment_blocks:
            if b.combined_confidence and b.combined_confidence < 0.7:
                # Prepare evidence 
                prompt = (
                    f"Classify semantic event at source_start={b.source_start} to {b.source_end} "
                    f"edited_start={b.edit_start} to {b.edit_end}. "
                    f"Evidence: transcript_conf={b.transcript_confidence}, visual_conf={b.visual_confidence}"
                )
                
                self.telemetry["flash_calls"] += 1
                res = self._call_agy(prompt, self.flash_model, schema_dict)
                
                if res and res.confidence < 0.8:
                    self.telemetry["escalations"] += 1
                    self.telemetry["pro_calls"] += 1
                    escalation_prompt = f"Escalation (Deep classify): {prompt}"
                    pro_res = self._call_agy(escalation_prompt, self.pro_model, schema_dict)
                    
                    if pro_res and pro_res.effect_type:
                        # Attempt to map to effect
                        try:
                            etype = EffectType(pro_res.effect_type)
                            target = EffectTargetType(pro_res.target) if pro_res.target else EffectTargetType.FULL_FRAME
                            effects.append(ObservedEffectContract(
                                id=str(uuid.uuid4()), pair_id="pair", effect_type=etype, target=target,
                                source_start=b.source_start, source_end=b.source_end, edit_start=b.edit_start, edit_end=b.edit_end,
                                confidence=pro_res.confidence, detection_method="antigravity_pro", is_manual_override=False, is_false_positive=False
                            ))
                        except ValueError:
                            pass
                elif res and res.effect_type:
                    try:
                        etype = EffectType(res.effect_type)
                        target = EffectTargetType(res.target) if res.target else EffectTargetType.FULL_FRAME
                        effects.append(ObservedEffectContract(
                            id=str(uuid.uuid4()), pair_id="pair", effect_type=etype, target=target,
                            source_start=b.source_start, source_end=b.source_end, edit_start=b.edit_start, edit_end=b.edit_end,
                            confidence=res.confidence, detection_method="antigravity_flash", is_manual_override=False, is_false_positive=False
                        ))
                    except ValueError:
                        pass
        return effects

    def infer_decisions(self, alignment_blocks: List[AlignmentBlockContract], effects: List[ObservedEffectContract]) -> List[ObservedEditorialDecisionContract]:
        decisions = []
        for b in alignment_blocks:
            decisions.append(ObservedEditorialDecisionContract(
                id=b.id,
                pair_id="pair",
                decision_type=EditorialDecisionType.RETAINED,
                source_start=b.source_start,
                source_end=b.source_end,
                edit_start=b.edit_start,
                edit_end=b.edit_end
            ))
        return decisions
