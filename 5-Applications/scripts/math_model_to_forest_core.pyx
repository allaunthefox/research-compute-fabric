import hashlib
import uuid


cdef object UUID_NAMESPACE = uuid.UUID("01000000-0000-4000-8000-000000000000")


def generate_uuid(str prefix, int index):
    """Generate deterministic UUID for equation forest entries."""
    cdef str seed = f"{prefix}-{index:04d}"
    return str(uuid.uuid5(UUID_NAMESPACE, seed))


def canonical_hash(str value):
    """Generate a stable canonical SHA-256 hash."""
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()
