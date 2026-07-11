import hashlib


def build_cache_key(task_type: str, model_name: str, prompt: str) -> str:
    """Deterministic cache key for a (task type, model, prompt) triple.

    Hashing the prompt keeps keys a fixed, bounded size regardless of
    document length, while `task_type`/`model_name` stay in the clear so
    keys are still greppable in cache backends that expose their key
    space (e.g. Redis `SCAN`)."""
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return f"ai_fabric:cache:{task_type}:{model_name}:{prompt_hash}"
