import hashlib

def get_style_cache_key(base_version: str, style_policy_id: str | None, style_version: int | None, dry_run: bool = False) -> str:
    """
    Returns an editorial_rules_version string that includes style policy data.
    If dry_run is True, appends '_dryrun' so it doesn't pollute the real cache.
    Changing the policy or version automatically invalidates the cache for M5/M8
    by producing a new hash.
    """
    parts = [base_version]
    if style_policy_id:
        parts.append(f"style_{style_policy_id}_v{style_version or 1}")
    if dry_run:
        parts.append("dryrun")
        
    return hashlib.md5("_".join(parts).encode("utf-8")).hexdigest()
