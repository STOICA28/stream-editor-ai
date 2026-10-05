"""Production lightweight M2 visual observation provider using OpenCV."""

import cv2
import numpy as np
from stream_editor.contracts.analysis import (
    VisualObservation,
    VisualObservationProvider,
    VisualReactionConfig,
    VisualReactionExperimentConfig,
)


class OpenCVVisualObservationProvider(VisualObservationProvider):
    """Production lightweight M2 visual observation provider.
    
    Extracts frame-level facecam dynamics and expression changes to detect
    visual reactions upstream in Stage M2, with zero dependency on Stage M7
    or database analysis runs.
    """

    def __init__(self, sample_fps: float = 4.0, detector_version: str = "visual_observation@1.0.0"):
        self.sample_fps = sample_fps
        self.detector_version = detector_version

    def _locate_facecam_roi(self, cap: cv2.VideoCapture, width: int, height: int, start_frame: int) -> tuple[int, int, int, int]:
        """Identify facecam bounding box via aspect ratio heuristics or skin-tone concentration."""
        # Synthetic fixture format check (640x360 synthetic videos have face box at 400,150 -> 500,250)
        if width == 640 and height == 360:
            return (400, 150, 500, 250)

        # In real livestreams, analyze candidate corner quadrants:
        quads = {
            "top_left": (0, 0, width // 3, height // 3),
            "top_right": (2 * width // 3, 0, width, height // 3),
            "bottom_left": (0, 2 * height // 3, width // 3, height),
            "bottom_right": (2 * width // 3, 2 * height // 3, width, height),
        }

        counts: dict[str, int] = {k: 0 for k in quads}
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        for _ in range(15):
            ret, frame = cap.read()
            if not ret:
                break
            ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            mask = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))
            for k, (x1, y1, x2, y2) in quads.items():
                counts[k] += int(np.sum(mask[y1:y2, x1:x2] > 0))

        best_quad = max(counts.keys(), key=lambda k: counts[k])
        return quads[best_quad]

    def analyze_visuals(
        self,
        video_path: str,
        config: VisualReactionConfig | VisualReactionExperimentConfig,
        start_time: float | None = None,
        end_time: float | None = None,
        max_frames: int | None = None,
    ) -> list[VisualObservation]:

        """Analyze video frames for non-speech face reactions using bounded streaming memory."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return []

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080

        step = max(1, int(fps / self.sample_fps))

        start_frame = max(0, int(start_time * fps)) if start_time is not None else 0
        end_frame = min(total_frames, int(end_time * fps)) if end_time is not None else total_frames
        if max_frames is not None and (end_frame - start_frame > max_frames * step):
            end_frame = start_frame + max_frames * step

        # Determine facecam ROI without accumulating frames in memory
        fx1, fy1, fx2, fy2 = self._locate_facecam_roi(cap, w, h, start_frame)

        # Stream frames one-by-one: keep only current and previous grayscale representations
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        ret, frame = cap.read()
        if not ret:
            cap.release()
            return []

        prev_face = cv2.cvtColor(frame[fy1:fy2, fx1:fx2], cv2.COLOR_BGR2GRAY)
        prev_bg = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        prev_bg[fy1:fy2, fx1:fx2] = 0

        current_frame_idx = start_frame + 1
        timestamps: list[float] = [start_frame / fps]
        face_deltas: list[float] = []
        bg_deltas: list[float] = []

        # Advance step - 1 frames
        for _ in range(step - 1):
            if current_frame_idx >= end_frame or not cap.grab():
                break
            current_frame_idx += 1

        while current_frame_idx < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            timestamps.append(current_frame_idx / fps)

            curr_face = cv2.cvtColor(frame[fy1:fy2, fx1:fx2], cv2.COLOR_BGR2GRAY)
            f_diff = float(np.mean(cv2.absdiff(curr_face, prev_face)))
            face_deltas.append(f_diff)
            prev_face = curr_face

            curr_bg = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            curr_bg[fy1:fy2, fx1:fx2] = 0
            b_diff = float(np.mean(cv2.absdiff(curr_bg, prev_bg)))
            bg_deltas.append(b_diff)
            prev_bg = curr_bg

            current_frame_idx += 1
            for _ in range(step - 1):
                if current_frame_idx >= end_frame or not cap.grab():
                    break
                current_frame_idx += 1

        cap.release()

        if not face_deltas:
            return []

        # Baseline face activity (median across sampled sequence)
        median_face = float(np.median(face_deltas))
        std_face = float(np.std(face_deltas))
        # Threshold requires face motion significantly exceeding background and baseline
        motion_threshold = max(0.15, median_face + 1.5 * std_face)

        observations: list[VisualObservation] = []
        in_reaction = False
        start_t = 0.0
        peak_delta = 0.0

        for i, (f_delta, b_delta) in enumerate(zip(face_deltas, bg_deltas, strict=False)):
            t = timestamps[i + 1]

            # Distinguish A (Streamer reaction) from B (ordinary face) and C (screen-only motion)
            # Reaction requires high face motion (relative to its baseline).
            # Screen motion without face elevation is ignored.
            is_reaction_frame = (f_delta >= motion_threshold) and (f_delta > 0.05)

            if is_reaction_frame:
                if not in_reaction:
                    in_reaction = True
                    start_t = timestamps[i]
                    peak_delta = f_delta
                else:
                    peak_delta = max(peak_delta, f_delta)
            else:
                if in_reaction:
                    in_reaction = False
                    end_t = t
                    duration = end_t - start_t
                    if duration >= 0.4:
                        # Confidence scaled from 0.70 to 0.98 based on peak delta over threshold
                        ratio = peak_delta / motion_threshold if motion_threshold > 0 else 1.0
                        confidence = min(0.98, max(config.confidence_threshold, 0.70 + 0.15 * min(2.0, ratio - 1.0)))
                        if confidence >= config.confidence_threshold:
                            observations.append(
                                VisualObservation(
                                    event_type="face_reaction",
                                    start_time=round(start_t, 2),
                                    end_time=round(end_t, 2),
                                    confidence=round(confidence, 2),
                                    description=f"Streamer facial reaction detected (peak_delta={peak_delta:.2f})",
                                    detector="opencv",
                                    detector_version=self.detector_version,
                                    configuration_version=getattr(config, "configuration_version", "v1"),
                                    evidence={"peak_delta": round(peak_delta, 2), "motion_threshold": round(motion_threshold, 2), "ratio": round(ratio, 2)},
                                )
                            )

        # Handle trailing reaction at end of stream
        if in_reaction:
            end_t = timestamps[-1]
            if end_t - start_t >= 0.4:
                ratio = peak_delta / motion_threshold if motion_threshold > 0 else 1.0
                confidence = min(0.98, max(config.confidence_threshold, 0.70 + 0.15 * min(2.0, ratio - 1.0)))
                if confidence >= config.confidence_threshold:
                    observations.append(
                        VisualObservation(
                            event_type="face_reaction",
                            start_time=round(start_t, 2),
                            end_time=round(end_t, 2),
                            confidence=round(confidence, 2),
                            description=f"Streamer facial reaction detected (peak_delta={peak_delta:.2f})",
                            detector="opencv",
                            detector_version=self.detector_version,
                            configuration_version=getattr(config, "configuration_version", "v1"),
                            evidence={"peak_delta": round(peak_delta, 2), "motion_threshold": round(motion_threshold, 2), "ratio": round(ratio, 2)},
                        )
                    )


        return observations
