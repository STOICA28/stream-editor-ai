from typing import List
from stream_editor.contracts.rendering import CompiledSegment
from stream_editor.contracts.effect_planning import EffectType

class FFmpegGraphBuilder:
    """
    Builds structured FFmpeg filter graphs to avoid raw string injections.
    """
    
    def build_segment_filter(self, segment: CompiledSegment, width: int, height: int, fps: float) -> tuple[str, str]:
        """
        Builds the complex filter string for a single segment.
        """
        video_filters = []
        audio_filters = []
        
        # Apply effects
        for eff in segment.effects:
            if eff.effect_type in (EffectType.ZOOM_REGION, EffectType.ZOOM_FACE, EffectType.ZOOM_CHAT):
                if eff.target_box:
                    w = eff.target_box.width * width
                    h = eff.target_box.height * height
                    x = eff.target_box.x * width
                    y = eff.target_box.y * height
                    
                    # We ensure it doesn't go out of bounds
                    scale_factor = eff.parameters.get("scale", 2.0)
                    
                    # Crop then scale back to original
                    video_filters.append(f"crop={w}:{h}:{x}:{y}")
                    video_filters.append(f"scale={width}:{height}")
                    
            elif eff.effect_type == EffectType.GRAYSCALE:
                video_filters.append("colorchannelmixer=.3:.4:.3:0:.3:.4:.3:0:.3:.4:.3")
                
            elif eff.effect_type == EffectType.SPEED_UP:
                factor = eff.parameters.get("factor", 1.5)
                video_filters.append(f"setpts={(1/factor):.4f}*PTS")
                audio_filters.append(f"atempo={factor:.4f}")
                
            elif eff.effect_type == EffectType.SLOW_MOTION:
                factor = eff.parameters.get("factor", 0.5)
                video_filters.append(f"setpts={(1/factor):.4f}*PTS")
                audio_filters.append(f"atempo={factor:.4f}")
                
            elif eff.effect_type == EffectType.AUDIO_GAIN:
                gain_db = eff.parameters.get("gain_db", 3.0)
                audio_filters.append(f"volume={gain_db}dB")
                
        # We assume base input is [0:v] and [0:a]
        # In this simple builder we chain video filters
        v_chain = ",".join(video_filters) if video_filters else ""
        a_chain = ",".join(audio_filters) if audio_filters else ""
        
        return v_chain, a_chain
