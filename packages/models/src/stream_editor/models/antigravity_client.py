import asyncio
import json
import os
import shutil
import hashlib
from typing import Dict, Any, Optional, Type, TypeVar, cast
from pydantic import BaseModel, ValidationError

T = TypeVar('T', bound=BaseModel)

class AIProviderError(Exception): pass
class AIProviderUnavailable(AIProviderError): pass
class AIAuthenticationError(AIProviderError): pass
class AIModelUnavailable(AIProviderError): pass
class AIProviderTimeout(AIProviderError): pass
class AIProviderCancelled(AIProviderError): pass
class AIInvalidStructuredOutput(AIProviderError): pass
class AIProviderExecutionError(AIProviderError): pass

_semaphore = asyncio.Semaphore(int(os.environ.get("ANTIGRAVITY_MAX_CONCURRENCY", "3")))

class AntigravityClient:
    def __init__(self, model: str = "gemini-3.1-pro-high", timeout: float = 60.0):
        self.model = model
        self.timeout = timeout
        self.bin_path = self._discover_bin()
        self.is_available = self.bin_path is not None
        
        self.telemetry: dict[str, Any] = {
            "provider": "antigravity",
            "model": self.model,
            "calls": 0,
            "duration": 0.0,
            "cache_hits": 0,
            "failures": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }
        self._cache: dict[str, Any] = {}

    def _discover_bin(self) -> Optional[str]:
        configured = os.getenv("ANTIGRAVITY_BIN")
        if configured is not None:
            return shutil.which(configured)
        
        for name in ["agy", "agy.exe", "agy.cmd"]:
            path = shutil.which(name)
            if path:
                return path
        return None

    def _generate_cache_key(self, schema_str: str, prompt: str) -> str:
        signature = f"antigravity|{self.model}|{schema_str}|{prompt}"
        return hashlib.sha256(signature.encode('utf-8')).hexdigest()

    async def health_check(self) -> Dict[str, Any]:
        if not self.is_available:
            return {
                "provider": "antigravity",
                "model": self.model,
                "installed": False,
                "authenticated": False,
                "available": False
            }
            
        try:
            proc = await asyncio.create_subprocess_exec(
                self.bin_path, "-p", "Reply with OK", "--output-format", "json",  # type: ignore[arg-type,arg-type]
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
            if proc.returncode != 0:
                return {
                    "provider": "antigravity",
                    "model": self.model,
                    "installed": True,
                    "authenticated": False,
                    "available": False
                }
            return {
                "provider": "antigravity",
                "model": self.model,
                "installed": True,
                "authenticated": True,
                "available": True
            }
        except Exception:
            return {
                "provider": "antigravity",
                "model": self.model,
                "installed": True,
                "authenticated": False,
                "available": False
            }

    async def generate_structured(self, prompt: str, schema_model: Type[T]) -> T:
        if not self.is_available:
            raise AIProviderUnavailable("Antigravity CLI (agy) not found in PATH or ANTIGRAVITY_BIN.")

        schema_dict = schema_model.model_json_schema()
        schema_str = json.dumps(schema_dict)
        cache_key = self._generate_cache_key(schema_str, prompt)

        if cache_key in self._cache:
            self.telemetry["cache_hits"] += 1
            return cast(T, self._cache[cache_key])

        async with _semaphore:
            self.telemetry["calls"] += 1
            
            try:
                proc = await asyncio.create_subprocess_exec(
                    self.bin_path,  # type: ignore[arg-type]
                    "-p", prompt, 
                    "--output-format", "json", 
                    "--json-schema", schema_str, 
                    "--model", self.model,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            except Exception as e:
                self.telemetry["failures"] += 1
                raise AIProviderExecutionError(f"Failed to start subprocess: {e}")

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            except asyncio.TimeoutError:
                proc.kill()
                self.telemetry["failures"] += 1
                raise AIProviderTimeout(f"Request timed out after {self.timeout}s")
            except asyncio.CancelledError:
                proc.kill()
                self.telemetry["failures"] += 1
                raise AIProviderCancelled("Request was cancelled")

            if proc.returncode != 0:
                self.telemetry["failures"] += 1
                raise AIProviderExecutionError(f"agy process failed with exit code {proc.returncode}")

            try:
                data = json.loads(stdout_bytes.decode('utf-8'))
            except json.JSONDecodeError:
                self.telemetry["failures"] += 1
                raise AIInvalidStructuredOutput("Could not parse JSON from CLI output")

            structured_output = data.get("structured_output", data)
            try:
                parsed = schema_model.model_validate(structured_output)
                self._cache[cache_key] = parsed
                
                usage = data.get("usage", {})
                if "prompt_tokens" in usage:
                    self.telemetry["input_tokens"] += usage["prompt_tokens"]
                if "completion_tokens" in usage:
                    self.telemetry["output_tokens"] += usage["completion_tokens"]
                if "total_tokens" in usage:
                    self.telemetry["total_tokens"] += usage["total_tokens"]
                    
                return parsed
            except ValidationError as e:
                self.telemetry["failures"] += 1
                raise AIInvalidStructuredOutput(f"Pydantic validation failed: {e}")

