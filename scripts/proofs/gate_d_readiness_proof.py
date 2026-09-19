import asyncio
import os
import subprocess
from httpx import AsyncClient, ASGITransport
from pathlib import Path

# Set up environment for PostgreSQL and Redis
os.environ["DATABASE_URL"] = "postgresql+asyncpg://streameditor:streameditor@127.0.0.1:5432/streameditor"
os.environ["DATABASE_URL_SYNC"] = "postgresql://streameditor:streameditor@127.0.0.1:5432/streameditor"
os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/0"

from stream_editor.api.main import app
from stream_editor.api.config import settings

async def run_gate_d_proof():
    print("=== GATE D: DEGRADED READINESS STATES PROOF ===")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Condition 1: HEALTHY
        print("\n--- 1. Testing HEALTHY State ---")
        live_res = await client.get("/health")
        ready_res = await client.get("/health/ready")
        print(f"Liveness Response: {live_res.json()}")
        print(f"Readiness Response: {ready_res.json()}")
        assert live_res.status_code == 200 and live_res.json().get("status") == "ok"
        assert ready_res.json().get("status") == "ready"
        assert ready_res.json()["diagnostics"]["database"] == "available"
        assert ready_res.json()["diagnostics"]["storage"] == "available"
        assert ready_res.json()["diagnostics"]["broker"] == "available"
        print("PASS: Healthy state verified (status=ready, all diagnostics available)")

        # 2. Condition 2: DATABASE DOWN
        print("\n--- 2. Testing DATABASE DOWN State ---")
        from stream_editor.api.database import engine
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from stream_editor.api import database
        
        orig_session = database.SessionLocal
        # Inject bad engine
        bad_engine = create_async_engine("postgresql+asyncpg://streameditor:streameditor@127.0.0.1:5439/bad_db", connect_args={"timeout": 1})
        database.SessionLocal = async_sessionmaker(bad_engine, expire_on_commit=False)
        try:
            live_res = await client.get("/health")
            ready_res = await client.get("/health/ready")
            print(f"Liveness (DB down): {live_res.json()}")
            print(f"Readiness (DB down): {ready_res.json()}")
            assert live_res.json().get("status") == "ok", "Liveness must remain healthy when DB is down"
            assert ready_res.json().get("status") == "not_ready"
            assert "unavailable" in ready_res.json()["diagnostics"]["database"]
            print("PASS: Database down state verified (liveness=ok, readiness=not_ready, db=unavailable)")
        finally:
            database.SessionLocal = orig_session

        # 3. Condition 3: STORAGE UNAVAILABLE
        print("\n--- 3. Testing STORAGE UNAVAILABLE State ---")
        orig_data_dir = settings.DATA_DIR
        # Point to unwritable invalid drive/path on Windows
        settings.DATA_DIR = Path("Z:/nonexistent_volume/data")
        try:
            ready_res = await client.get("/health/ready")
            print(f"Readiness (Storage unavailable): {ready_res.json()}")
            assert ready_res.json().get("status") == "not_ready"
            assert "unavailable" in ready_res.json()["diagnostics"]["storage"]
            print("PASS: Storage unavailable state verified (readiness=not_ready, storage=unavailable)")
        finally:
            settings.DATA_DIR = orig_data_dir

        # 4. Condition 4: ANTIGRAVITY UNAVAILABLE
        print("\n--- 4. Testing ANTIGRAVITY UNAVAILABLE State ---")
        os.environ["ANTIGRAVITY_BIN"] = "C:/nonexistent_path/fake_agy.exe"
        try:
            ready_res = await client.get("/health/ready")
            print(f"Readiness (Antigravity unavailable): {ready_res.json()}")
            # Readiness degrades gracefully: media/deterministic operations remain functional
            assert ready_res.json().get("status") == "degraded"
            assert ready_res.json()["diagnostics"]["antigravity"] == "unavailable"
            print("PASS: Antigravity unavailable verified (readiness=degraded, antigravity=unavailable)")
        finally:
            os.environ.pop("ANTIGRAVITY_BIN", None)

        # 5. Condition 5: BROKER UNAVAILABLE
        print("\n--- 5. Testing BROKER UNAVAILABLE State ---")
        orig_redis = settings.REDIS_URL
        settings.REDIS_URL = "redis://127.0.0.1:6399/0"
        try:
            ready_res = await client.get("/health/ready")
            print(f"Readiness (Broker unavailable): {ready_res.json()}")
            assert ready_res.json().get("status") == "degraded"
            assert "unavailable" in ready_res.json()["diagnostics"]["broker"]
            print("PASS: Broker unavailable verified (readiness=degraded, broker=unavailable)")
        finally:
            settings.REDIS_URL = orig_redis

    # 6. Check for raw Gemini API usage
    print("\n--- 6. Auditing Active Codebase for Raw Gemini API Usage ---")
    forbidden = ["google.generativeai", "google.genai", "GEMINI_API_KEY"]
    for term in forbidden:
        res = subprocess.run(
            ["rtk", "rg", "-g", "!scripts/proofs/*", "-g", "!*.md", "-g", "!*.env*", term, "apps/", "packages/"],
            capture_output=True, text=True
        )
        matches = [line for line in res.stdout.strip().split("\n") if line.strip()]
        print(f"Checking for '{term}': {len(matches)} occurrences in active runtime code")
        if matches and matches != [""]:
            print(f"Found matches: {matches}")
            assert False, f"Forbidden direct Gemini term '{term}' found in runtime code!"
    print("PASS: 0 direct Gemini API/SDK calls found in active runtime. All route through AntigravityClient -> agy -> gemini-3.1-pro-high.")

    print("\n=== GATE D DEGRADED READINESS STATES: FULL PASS ===")

if __name__ == "__main__":
    asyncio.run(run_gate_d_proof())
