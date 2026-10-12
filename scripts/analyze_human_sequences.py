import json
from pathlib import Path
from collections import defaultdict

def run_alignment_analysis():
    with open('cache/test_blocks.json') as f:
        test_blocks = json.load(f)

    with open('cache/m10_alignment_state.json') as f:
        m10_state = json.load(f)
    m10_blocks = m10_state.get('blocks', [])

    print(f"Total test_blocks: {len(test_blocks)}")
    print(f"Total m10_blocks: {len(m10_blocks)}")

    # Merge / combine high-confidence blocks from both sources
    # Sort test blocks by edit_start
    sorted_tb = sorted(test_blocks, key=lambda b: (b['edit_start'], b['source_start']))
    
    # Analyze edit coverage
    edit_durations = [b['edit_end'] - b['edit_start'] for b in sorted_tb]
    source_durations = [b['source_end'] - b['source_start'] for b in sorted_tb]
    
    total_edit_time = sum(edit_durations)
    total_source_time = sum(source_durations)
    print(f"Sum of edit block intervals: {total_edit_time:.2f}s")
    print(f"Sum of source block intervals: {total_source_time:.2f}s")
    
    # Source temporal distribution across 5 hours (18675s)
    # Bin into 15-minute chapters (900s each) -> ~21 chapters
    source_bins = defaultdict(float)
    for b in sorted_tb:
        s_mid = (b['source_start'] + b['source_end']) / 2.0
        bin_idx = int(s_mid // 900)
        source_bins[bin_idx] += (b['source_end'] - b['source_start'])
        
    print("\nSource Coverage by 15-Minute Chapters (900s):")
    for bin_idx in sorted(source_bins.keys()):
        start_min = bin_idx * 15
        end_min = (bin_idx + 1) * 15
        retained_sec = source_bins[bin_idx]
        print(f"Ch {bin_idx:02d} [{start_min:03d}m - {end_min:03d}m]: {retained_sec:6.1f}s retained ({retained_sec/900.0*100:4.1f}%)")

    # Group adjacent blocks into continuous retained sequences
    # If gap in edit < 1.0s and gap in source < 2.0s, merge into contiguous sequence
    continuous_sequences = []
    curr_seq = None

    for b in sorted_tb:
        es, ee = b['edit_start'], b['edit_end']
        ss, se = b['source_start'], b['source_end']
        if curr_seq is None:
            curr_seq = {
                'edit_start': es, 'edit_end': ee,
                'source_start': ss, 'source_end': se,
                'block_count': 1
            }
        else:
            edit_gap = es - curr_seq['edit_end']
            source_gap = ss - curr_seq['source_end']
            # If contiguous in both edit and source
            if abs(edit_gap) < 1.5 and abs(source_gap) < 3.0 and source_gap >= -0.5:
                curr_seq['edit_end'] = max(curr_seq['edit_end'], ee)
                curr_seq['source_end'] = max(curr_seq['source_end'], se)
                curr_seq['block_count'] += 1
            else:
                continuous_sequences.append(curr_seq)
                curr_seq = {
                    'edit_start': es, 'edit_end': ee,
                    'source_start': ss, 'source_end': se,
                    'block_count': 1
                }
    if curr_seq:
        continuous_sequences.append(curr_seq)

    print(f"\nGrouped into {len(continuous_sequences)} continuous sequences")
    seq_durations = [s['source_end'] - s['source_start'] for s in continuous_sequences]
    seq_durations.sort()
    if seq_durations:
        print(f"Sequence durations: min={seq_durations[0]:.1f}s, median={seq_durations[len(seq_durations)//2]:.1f}s, max={seq_durations[-1]:.1f}s, mean={sum(seq_durations)/len(seq_durations):.1f}s")

    # Show first 15 sequences (Intro and Game Start)
    print("\nFirst 15 continuous sequences in the human edit:")
    for i, s in enumerate(continuous_sequences[:15]):
        s_dur = s['source_end'] - s['source_start']
        e_dur = s['edit_end'] - s['edit_start']
        print(f"Seq {i+1:02d}: edit [{s['edit_start']:6.1f}s - {s['edit_end']:6.1f}s] ({e_dur:4.1f}s) <- source [{s['source_start']:7.1f}s - {s['source_end']:7.1f}s] ({s_dur:5.1f}s, {s['block_count']} blocks)")

if __name__ == '__main__':
    run_alignment_analysis()
