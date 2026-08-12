import torch


def resolve_device(requested: str) -> str:
    """Maps 'auto' to the best available backend (cuda > mps > cpu)."""
    if requested and requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "cuda:0"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"
