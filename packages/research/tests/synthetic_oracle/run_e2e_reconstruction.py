import json
import os
from stream_editor.research.providers.gemini import GeminiReferenceProvider

def run():
    print("Running E2E Reconstruction Test on Synthetic Media...")
    
    fixtures_dir = "tests/fixtures"
    s_mp4 = os.path.join(fixtures_dir, "source.mp4")
    e_mp4 = os.path.join(fixtures_dir, "edited.mp4")
    gt_file = os.path.join(fixtures_dir, "ground_truth.json")
    
    if not os.path.exists(gt_file):
        print("Ground truth not found. Did you generate media?")
        return
        
    with open(gt_file, "r") as f:
        gt = json.load(f)
        
    provider = GeminiReferenceProvider(api_key=None) # No real API call for synthetic
    
    blocks = provider.align_media(s_mp4, e_mp4)
    effects = provider.detect_effects(blocks, s_mp4, e_mp4)
    
    print("\n--- Ground Truth Blocks ---")
    for b in gt["blocks"]:
        print(f"[{b['source_start']:.1f} -> {b['source_end']:.1f}] Speed: {b['speed_ratio']:.1f}")
        
    print("\n--- Pipeline Blocks ---")
    for b in blocks:
        print(f"[{b.source_start:.1f} -> {b.source_end:.1f}] Speed: {b.speed_ratio:.1f}")
        
    print("\n--- Ground Truth Effects ---")
    for e in gt["effects"]:
        print(f"{e['effect_type']} | Source: {e['source_start']:.1f}->{e['source_end']:.1f}")
        
    print("\n--- Pipeline Effects ---")
    for e in effects:
        print(f"{e.effect_type} | Source: {e.source_start:.1f}->{e.source_end:.1f}")
        
    # Simple evaluation
    matched_blocks = 0
    total_error = 0.0
    for tb in gt["blocks"]:
        if tb["speed_ratio"] == 0.0:
            continue
        best_diff = 999.0
        for pb in blocks:
            diff = abs(tb["source_start"] - pb.source_start) + abs(tb["source_end"] - pb.source_end)
            if diff < best_diff:
                best_diff = diff
        if best_diff < 0.5:
            matched_blocks += 1
            total_error += best_diff
            
    print(f"\nBlock Recall: {matched_blocks} / {len([b for b in gt['blocks'] if b['speed_ratio'] > 0])}")
    print(f"Average Block Timing Error: {total_error / matched_blocks if matched_blocks else 0:.3f}s")
    
    matched_eff = 0
    for te in gt["effects"]:
        best_diff = 999.0
        for pe in effects:
            if pe.effect_type == te["effect_type"]:
                diff = abs(te["source_start"] - pe.source_start) + abs(te["source_end"] - pe.source_end)
                if diff < best_diff:
                    best_diff = diff
        if best_diff < 0.5:
            matched_eff += 1
            
    print(f"Effect Recall: {matched_eff} / {len(gt['effects'])}")
    print(f"Telemetry: {provider.telemetry}")

if __name__ == "__main__":
    run()
