import json
from pathlib import Path

def analyze_early_blocks():
    with open('cache/test_blocks.json') as f:
        tb = json.load(f)

    early_edit_blocks = [b for b in tb if b['edit_start'] < 120.0]
    print(f"Total blocks with edit_start < 120s in test_blocks: {len(early_edit_blocks)}")
    for b in sorted(early_edit_blocks, key=lambda x: x['edit_start'])[:30]:
        es = b['edit_start']
        ee = b['edit_end']
        ss = b['source_start']
        se = b['source_end']
        conf = b.get('combined_confidence')
        method = b.get('method')
        print(f"edit: [{es:.1f}s - {ee:.1f}s] -> source: [{ss:.1f}s - {se:.1f}s] (edit_dur: {ee-es:.1f}s, conf: {conf}) method: {method}")

    with open('cache/m10_alignment_state.json') as f:
        m10 = json.load(f)
    m10_blocks = m10.get('blocks', [])
    early_m10 = [b for b in m10_blocks if b['edit_start'] < 120.0]
    print(f"\nTotal blocks with edit_start < 120s in m10_alignment_state: {len(early_m10)}")
    for b in sorted(early_m10, key=lambda x: x['edit_start'])[:30]:
        es = b['edit_start']
        ee = b['edit_end']
        ss = b['source_start']
        se = b['source_end']
        conf = b.get('combined_confidence')
        method = b.get('method')
        print(f"edit: [{es:.1f}s - {ee:.1f}s] -> source: [{ss:.1f}s - {se:.1f}s] (edit_dur: {ee-es:.1f}s, conf: {conf}) method: {method}")

if __name__ == '__main__':
    analyze_early_blocks()
