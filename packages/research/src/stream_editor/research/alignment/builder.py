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
        t_blocks = self.transcript_aligner.align(source_asset_id, edited_asset_id)
        v_blocks = self.visual_aligner.align(source_asset_id, edited_asset_id)
        a_blocks = self.audio_aligner.align(source_asset_id, edited_asset_id)
        
        merged = []
        for tb in t_blocks:
            tb.run_id = run_id
            merged.append(tb)
            
        for vb in v_blocks:
            vb.run_id = run_id
            overlap_dur = 0
            for mb in merged:
                start = max(vb.edit_start, mb.edit_start)
                end = min(vb.edit_end, mb.edit_end)
                if end > start:
                    overlap_dur += (end - start)
            if overlap_dur < (vb.edit_end - vb.edit_start) * 0.5:
                merged.append(vb)
                
        for ab in a_blocks:
            ab.run_id = run_id
            overlap_dur = 0
            for mb in merged:
                start = max(ab.edit_start, mb.edit_start)
                end = min(ab.edit_end, mb.edit_end)
                if end > start:
                    overlap_dur += (end - start)
            if overlap_dur < (ab.edit_end - ab.edit_start) * 0.5:
                merged.append(ab)
                
        merged.sort(key=lambda x: x.edit_start)
        
        final_blocks = []
        if not merged:
            return []
            
        current = merged[0]
        for i in range(1, len(merged)):
            nxt = merged[i]
            
            s_gap = nxt.source_start - current.source_end
            e_gap = nxt.edit_start - current.edit_end
            
            # Allow merging across different methods if speed is the same
            if current.speed_ratio == nxt.speed_ratio and abs(s_gap - e_gap) < 0.5 and s_gap < 1.0:
                current.source_end = max(current.source_end, nxt.source_end)
                current.edit_end = max(current.edit_end, nxt.edit_end)
                current.method = "combined"
            else:
                final_blocks.append(current)
                current = nxt
                
        final_blocks.append(current)
        
        clean = []
        if not final_blocks:
            return clean
            
        current = final_blocks[0]
        for i in range(1, len(final_blocks)):
            nxt = final_blocks[i]
            
            if nxt.edit_start < current.edit_end:
                overlap = current.edit_end - nxt.edit_start
                nxt.edit_start += overlap
                nxt.source_start += overlap * nxt.speed_ratio
                if nxt.edit_start >= nxt.edit_end:
                    continue 
                    
            s_gap = nxt.source_start - current.source_end
            e_gap = nxt.edit_start - current.edit_end
            
            if current.speed_ratio == nxt.speed_ratio and abs(s_gap - e_gap) < 0.2 and 0 <= s_gap < 1.0:
                current.source_end = nxt.source_end
                current.edit_end = nxt.edit_end
                current.method = "mixed"
            else:
                clean.append(current)
                current = nxt
        clean.append(current)
            
        return clean
