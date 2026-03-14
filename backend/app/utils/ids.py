from uuid import uuid4


def generate_job_id() -> str:
    """Create a short, collision-resistant job identifier."""
    return uuid4().hex[:12]
