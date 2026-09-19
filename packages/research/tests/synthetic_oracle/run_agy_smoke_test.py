import os
import json
import uuid
import sys
from stream_editor.contracts.research import AlignmentBlockContract
from stream_editor.research.providers.antigravity import AntigravityReferenceProvider  # type: ignore[import-untyped]

def run_smoke_test():  # type: ignore[no-untyped-def]
    print("--- AntigravityReferenceProvider Smoke Test ---")
    provider = AntigravityReferenceProvider(
        flash_model="gemini-1.5-flash-latest",
        pro_model="gemini-1.5-pro-latest"
    )
    
    if not provider.is_available:
        print("Antigravity CLI (agy) is NOT available or not authenticated. Falling back cleanly.")
        print(f"Telemetry: {provider.telemetry}")
        print("M10.3 LOCAL VALIDATION: BLOCKED (agy CLI unavailable in this environment)")
        return

    print("Antigravity CLI is available. Running real headless calls...")
    
    b1 = AlignmentBlockContract(
        id=str(uuid.uuid4()),
        run_id="run",
        source_start=10.0,
        source_end=15.0,
        edit_start=5.0,
        edit_end=10.0,
        audio_confidence=0.5,
        transcript_confidence=0.5,
        visual_confidence=0.5,
        combined_confidence=0.5,
        speed_ratio=1.0,
        method="combined",
        is_manual_override=False
    )
    
    # 1. Flash request
    print("\n[Test 1] Detecting effects (Ambiguous -> Flash)")
    effects = provider.detect_effects([b1], "dummy.mp4", "dummy.mp4")
    print(f"Detected {len(effects)} effects.")
    for e in effects:
        print(f"  Type: {e.effect_type}, Conf: {e.confidence}, Method: {e.detection_method}")
    print("\n--- Telemetry after Request 1 ---")
    print(provider.telemetry)
    
    # 2. Cache request
    print("\n[Test 2] Exact same request (Cache Hit expected)")
    effects_cached = provider.detect_effects([b1], "dummy.mp4", "dummy.mp4")
    print(f"Detected {len(effects_cached)} effects.")
    print("\n--- Telemetry after Request 2 ---")
    print(provider.telemetry)
    
    # 3. Validation success
    if provider.telemetry["cache_hits"] > 0 and (provider.telemetry["flash_calls"] > 0 or provider.telemetry["pro_calls"] > 0):
        print("\nM10.3 LOCAL VALIDATION: SUCCESS")
    else:
        print("\nM10.3 LOCAL VALIDATION: FAILED")

if __name__ == "__main__":
    run_smoke_test()  # type: ignore[no-untyped-call]
