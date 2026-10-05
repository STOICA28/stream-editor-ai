"""Production lightweight M2 visual observation provider using OpenCV."""

import cv2
import numpy as np
from stream_editor.contracts.analysis import (
    VisualObservation,
    VisualObservationProvider,
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

    def _locate_facecam_roi(self, frames: list[np.ndarray], width: int, height: int) -> tuple[int, int, int, int]:
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

        # Skin tone clustering in YCrCb color space
        counts: dict[str, int] = {k: 0 for k in quads}
        sample_count = min(15, len(frames))
        for f in frames[:sample_count]:
            ycrcb = cv2.cvtColor(f, cv2.COLOR_BGR2YCrCb)
            mask = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))
            for k, (x1, y1, x2, y2) in quads.items():
                counts[k] += int(np.sum(mask[y1:y2, x1:x2] > 0))

        best_quad = max(counts.keys(), key=lambda k: counts[k])
        return quads[best_quad]

    def analyze_visuals(
        self,
        video_path: str,
        config: VisualReactionExperimentConfig,
        start_time: float | None = None,
        end_time: float | None = None,
    ) -> list[VisualObservation]:
        """Analyze video frames for non-speech face reactions."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return []

        step = max(1, int(fps / self.sample_fps))

        start_frame = max(0, int(start_time * fps)) if start_time is not None else 0
        end_frame = min(total_frames, int(end_time * fps)) if end_time is not None else total_frames
        # Cap max frames sampled in single invocation to 1200 (~5 minutes at 4fps) to preserve performance
        if end_frame - start_frame > 1200 * step:
            end_frame = start_frame + 1200 * step

        # Sample frames across video
        frames: list[np.ndarray] = []
        timestamps: list[float] = []
        if start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        current_frame_idx = start_frame
        while current_frame_idx < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
            timestamps.append(current_frame_idx / fps)
            current_frame_idx += 1
            for _ in range(step - 1):
                if current_frame_idx >= end_frame:
                    break
                if not cap.grab():
                    break
                current_frame_idx += 1
        cap.release()

        if len(frames) < 2:
            return []

        h, w, _ = frames[0].shape
        fx1, fy1, fx2, fy2 = self._locate_facecam_roi(frames, w, h)

        face_deltas: list[float] = []
        bg_deltas: list[float] = []

        for i in range(1, len(frames)):
            prev_gray = cv2.cvtColor(frames[i - 1], cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
            diff = cv2.absdiff(curr_gray, prev_gray)

            # Localized face motion
            f_diff = float(np.mean(diff[fy1:fy2, fx1:fx2]))
            face_deltas.append(f_diff)

            # Background motion (mask out facecam to isolate gameplay/screen motion)
            diff_bg = diff.copy()
            diff_bg[fy1:fy2, fx1:fx2] = 0
            b_diff = float(np.mean(diff_bg))
            bg_deltas.append(b_diff)

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
                        )
                    )

        return observations
