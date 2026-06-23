"""
Device auto-detection utility.

Provides a single DEVICE constant used across the codebase so that
GPU acceleration is transparently enabled whenever available.

Priority: CUDA → MPS (Apple Silicon) → CPU
"""


def get_optimal_device() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


DEVICE: str = get_optimal_device()
