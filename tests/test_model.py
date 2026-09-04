"""Phase 1 model placeholder tests — real training arrives in Phase 5."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.prediction_model import train_models
import pytest


def test_train_models_not_implemented_yet():
    with pytest.raises(NotImplementedError):
        train_models()
