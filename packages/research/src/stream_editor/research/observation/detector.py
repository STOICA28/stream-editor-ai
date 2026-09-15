import cv2
import numpy as np
from typing import List
from stream_editor.contracts.research import AlignmentBlockContract, ObservedEffectContract
from stream_editor.contracts.effect_planning import EffectType, EffectTargetType
import uuid

class LocalEffectDetector:
    def detect(self, blocks: List[AlignmentBlockContract], source_path: str, edited_path: str) -> List[ObservedEffectContract]:
        effects = []
        
        cap_s = cv2.VideoCapture(source_path)
        cap_e = cv2.VideoCapture(edited_path)
        
        fps = cap_s.get(cv2.CAP_PROP_FPS)
        
        for b in blocks:
            if b.speed_ratio > 1.5:
                effects.append(ObservedEffectContract(
                    id=str(uuid.uuid4()), pair_id="pair", effect_type=EffectType.SPEED_UP, target=EffectTargetType.FULL_FRAME,
                    source_start=b.source_start, source_end=b.source_end, edit_start=b.edit_start, edit_end=b.edit_end,
                    confidence=0.95, detection_method="alignment", is_manual_override=False, is_false_positive=False
                ))
            elif 0.0 < b.speed_ratio < 0.8:
                effects.append(ObservedEffectContract(
                    id=str(uuid.uuid4()), pair_id="pair", effect_type=EffectType.SLOW_MOTION, target=EffectTargetType.FULL_FRAME,
                    source_start=b.source_start, source_end=b.source_end, edit_start=b.edit_start, edit_end=b.edit_end,
                    confidence=0.95, detection_method="alignment", is_manual_override=False, is_false_positive=False
                ))
                
            # Sample frames every 0.5s to detect effects
            step = 0.5
            current_src = b.source_start
            
            current_effect = None
            
            while current_src < b.source_end - 0.1:
                current_edit = b.edit_start + (current_src - b.source_start) / b.speed_ratio if b.speed_ratio > 0 else b.edit_start
                
                cap_s.set(cv2.CAP_PROP_POS_MSEC, current_src * 1000)
                ret_s, frame_s = cap_s.read()
                
                cap_e.set(cv2.CAP_PROP_POS_MSEC, current_edit * 1000)
                ret_e, frame_e = cap_e.read()
                
                detected_type = None
                detected_target = None
                scale = None
                
                if ret_s and ret_e:
                    gray_e = cv2.cvtColor(frame_e, cv2.COLOR_BGR2GRAY)
                    re_bgr = cv2.cvtColor(gray_e, cv2.COLOR_GRAY2BGR)
                    diff_gray = np.sum(np.abs(frame_e.astype(int) - re_bgr.astype(int)))
                    
                    # Screen crop
                    screen_crop = frame_s[0:300, 0:300]
                    screen_crop_resized = cv2.resize(screen_crop, (640, 360))
                    diff_screen = np.sum(np.abs(frame_e.astype(int) - screen_crop_resized.astype(int)))
                    
                    # Face zoom
                    cx, cy = 450, 200
                    sc = 1.5
                    w, h = 640, 360
                    w_new, h_new = int(w / sc), int(h / sc)
                    x1 = max(0, cx - w_new // 2)
                    y1 = max(0, cy - h_new // 2)
                    x2 = min(w, x1 + w_new)
                    y2 = min(h, y1 + h_new)
                    face_crop = frame_s[y1:y2, x1:x2]
                    face_crop_resized = cv2.resize(face_crop, (w, h))
                    diff_face = np.sum(np.abs(frame_e.astype(int) - face_crop_resized.astype(int)))
                    
                    if diff_gray < 1000:
                        detected_type = EffectType.GRAYSCALE
                        detected_target = EffectTargetType.FULL_FRAME
                    elif diff_screen < 1000000:
                        detected_type = EffectType.CROP_FOCUS
                        detected_target = EffectTargetType.SCREEN_REGION
                    elif diff_face < 1000000:
                        detected_type = EffectType.ZOOM_FACE
                        detected_target = EffectTargetType.FACECAM
                        scale = sc
                        
                if detected_type != current_effect:
                    if current_effect is not None:
                        # close previous effect
                        effects[-1].source_end = current_src
                        effects[-1].edit_end = current_edit
                    if detected_type is not None:
                        # start new effect
                        effects.append(ObservedEffectContract(
                            id=str(uuid.uuid4()), pair_id="pair", effect_type=detected_type, target=detected_target,
                            source_start=current_src, source_end=b.source_end, edit_start=current_edit, edit_end=b.edit_end,
                            confidence=0.9, detection_method="visual", is_manual_override=False, is_false_positive=False
                        ))
                    current_effect = detected_type
                    
                current_src += step
                
        cap_s.release()
        cap_e.release()
        
        return effects
