import hashlib
from typing import Callable, Any
from stream_editor.api.models.project import ModelResultCache as DBModelResultCache

class ModelResultCache:
    @staticmethod
    def generate_key(provider: str, model: str, prompt_version: str, input_hash: str, editorial_rules_version: str | None) -> str:
        parts = [provider, model, prompt_version, input_hash, editorial_rules_version or ""]
        return hashlib.sha256("_".join(parts).encode("utf-8")).hexdigest()

    @staticmethod
    def get_or_set(
        db_session: Any, 
        cache_key: str, 
        provider: str, 
        model: str, 
        prompt_version: str, 
        editorial_rules_version: str | None, 
        compute_fn: Callable[[], dict]
    ) -> tuple[dict, bool]:
        
        cached = db_session.query(DBModelResultCache).filter_by(cache_key=cache_key).first()
        if cached and cached.result is not None:
            return cached.result, True
            
        result = compute_fn()
        
        new_entry = DBModelResultCache(
            cache_key=cache_key,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            editorial_rules_version=editorial_rules_version,
            result=result
        )
        db_session.add(new_entry)
        db_session.commit()
        
        return result, False
