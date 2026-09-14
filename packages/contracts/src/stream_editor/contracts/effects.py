from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EffectType(str, Enum):
    cut = "cut"
    zoom_region = "zoom_region"
    zoom_face = "zoom_face"
    zoom_chat = "zoom_chat"
    crop = "crop"
    grayscale = "grayscale"
    freeze_frame = "freeze_frame"
    slow_motion = "slow_motion"
    speed_up = "speed_up"
    text_overlay = "text_overlay"
    subtitle = "subtitle"
    image_overlay = "image_overlay"
    audio_gain = "audio_gain"
    audio_duck = "audio_duck"
    fade = "fade"
    blur = "blur"
    highlight_region = "highlight_region"

class ZoomRegionParams(BaseModel):
    x: float
    y: float
    width: float
    height: float
    scale: float = Field(ge=1.0, le=3.0)
    duration_seconds: float

class ZoomFaceParams(BaseModel):
    scale: float = Field(ge=1.2, le=2.0)
    duration_seconds: float = Field(ge=0.5, le=5.0)
    interpolation: str

class ZoomChatParams(BaseModel):
    scale: float = Field(ge=1.2, le=1.6)
    duration_seconds: float

class GrayscaleParams(BaseModel):
    duration_seconds: float
    intensity: float = Field(ge=0.0, le=1.0)

class FreezeFrameParams(BaseModel):
    duration_seconds: float = Field(ge=0.5, le=3.0)

class SlowMotionParams(BaseModel):
    speed: float = Field(ge=0.25, le=0.75)

class SpeedUpParams(BaseModel):
    speed: float = Field(ge=1.25, le=4.0)

class TextOverlayParams(BaseModel):
    text: str
    x: float
    y: float
    font_size: int
    duration_seconds: float
    style: str

class SubtitleParams(BaseModel):
    text: str
    start_seconds: float
    end_seconds: float

class AudioGainParams(BaseModel):
    gain_db: float = Field(ge=-20.0, le=20.0)

class AudioDuckParams(BaseModel):
    target_gain_db: float
    duration_seconds: float

class FadeParams(BaseModel):
    direction: str
    duration_seconds: float

class BlurParams(BaseModel):
    radius: float
    duration_seconds: float

class CutParams(BaseModel):
    pass

class CropParams(BaseModel):
    pass

class ImageOverlayParams(BaseModel):
    pass

class HighlightRegionParams(BaseModel):
    pass

class Effect(BaseModel):
    effect_type: EffectType
    params: dict[str, Any]
    start_seconds: float
    end_seconds: float

def validate_effect(effect: Effect) -> None:
    mapping = {
        EffectType.zoom_region: ZoomRegionParams,
        EffectType.zoom_face: ZoomFaceParams,
        EffectType.zoom_chat: ZoomChatParams,
        EffectType.grayscale: GrayscaleParams,
        EffectType.freeze_frame: FreezeFrameParams,
        EffectType.slow_motion: SlowMotionParams,
        EffectType.speed_up: SpeedUpParams,
        EffectType.text_overlay: TextOverlayParams,
        EffectType.subtitle: SubtitleParams,
        EffectType.audio_gain: AudioGainParams,
        EffectType.audio_duck: AudioDuckParams,
        EffectType.fade: FadeParams,
        EffectType.blur: BlurParams,
        EffectType.cut: CutParams,
        EffectType.crop: CropParams,
        EffectType.image_overlay: ImageOverlayParams,
        EffectType.highlight_region: HighlightRegionParams,
    }
    model = mapping[effect.effect_type]
    model(**effect.params)
