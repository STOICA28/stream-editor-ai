from typing import List
from stream_editor.contracts.analysis import SceneDetectionProvider, SceneConfig, Scene

class ScenedetectProvider(SceneDetectionProvider):
    def detect_scenes(self, video_path: str, config: SceneConfig) -> List[Scene]:
        from scenedetect import detect, ContentDetector
        
        detector = ContentDetector(threshold=config.threshold, min_scene_len=config.min_scene_len)
        scene_list = detect(video_path, detector)
        
        scenes = []
        for scene in scene_list:
            start_time = scene[0].get_seconds()
            end_time = scene[1].get_seconds()
            scenes.append(Scene(start_time=start_time, end_time=end_time))
            
        return scenes
