"""Memory subsystem: conversation, case, workflow and user memory.

All four are thin, purpose-specific wrappers around a single
`MemoryStorePort` (key/value with namespacing), so a new storage backend
only needs to be written once (see `in_memory_store.py`, `redis_store.py`).
"""
