from typing import List
from stream_editor.contracts.research import AlignmentBlockContract
from stream_editor.research.alignment.transcript import TranscriptAligner
from stream_editor.research.alignment.audio import AudioAligner
from stream_editor.research.alignment.visual import VisualAligner
import uuid

class MultiSignalAlignmentBuilder:
    def __init__(self) -> None:
        self.transcript_aligner = TranscriptAligner()
        self.audio_aligner = AudioAligner()
        self.visual_aligner = VisualAligner()
        
    def build(self, source_asset_id: str, edited_asset_id: str, run_id: str = "run") -> List[AlignmentBlockContract]:
        print("Builder: Running Audio Aligner...")
        a_blocks = self.audio_aligner.align(source_asset_id, edited_asset_id)
        
        print("Builder: Running Continuity Filter on Audio Blocks...")
        a_blocks.sort(key=lambda x: x.edit_start)
        sequences = []
        current_seq = []  # type: ignore[var-annotated]
        for b in a_blocks:
            if not current_seq:
                current_seq.append(b)
                continue
            prev = current_seq[-1]
            edit_diff = b.edit_start - prev.edit_start
            source_diff = b.source_start - prev.source_start
            if edit_diff > 0 and 0.5 <= source_diff / edit_diff <= 1.5:
                current_seq.append(b)
            else:
                sequences.append(current_seq)
                current_seq = [b]
        if current_seq: sequences.append(current_seq)
        
        filtered_audio_blocks = []
        for seq in sequences:
            if len(seq) >= 2:
                filtered_audio_blocks.extend(seq)
                
        # Calculate unmatched intervals
        mapped_intervals = []
        current_interval = None
        for b in filtered_audio_blocks:
            if not current_interval:
                current_interval = [b.edit_start, b.edit_end]
                continue
            if b.edit_start <= current_interval[1] + 1.0:
                current_interval[1] = max(current_interval[1], b.edit_end)
            else:
                mapped_intervals.append(current_interval)
                current_interval = [b.edit_start, b.edit_end]
        if current_interval: mapped_intervals.append(current_interval)
        
        unmatched_intervals = []
        last_end = 0.0
        for start, end in mapped_intervals:
            if start > last_end:
                unmatched_intervals.append([last_end, start])
            last_end = end
        if last_end < 2400.0: # Edited video is 40 mins
            unmatched_intervals.append([last_end, 2400.0])
            
        print(f"Builder: Found {len(unmatched_intervals)} unmatched intervals.")
        
        v_blocks = self.visual_aligner.align(source_asset_id, edited_asset_id, unmatched_intervals)
        
        merged = filtered_audio_blocks + v_blocks
        merged.sort(key=lambda x: x.edit_start)
        
        for mb in merged:
            mb.run_id = run_id
            
        return merged
