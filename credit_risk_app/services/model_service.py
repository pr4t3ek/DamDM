"""Loads the cached model training results produced by scripts/train_models.py."""
import json
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
RESULTS_CACHE = DATA_DIR / "model_results.json"

_NOT_TRAINED = (
    "{path} not found. Run `python credit_risk_app/scripts/train_models.py` "
    "(after prepare_data.py and build_features.py) to train the models."
)

MODEL_ORDER = ["logistic_regression", "decision_tree", "random_forest", "xgboost"]

_results = None


def is_trained() -> bool:
    return RESULTS_CACHE.exists()


def get_results() -> dict:
    global _results
    if _results is None:
        if not RESULTS_CACHE.exists():
            raise FileNotFoundError(_NOT_TRAINED.format(path=RESULTS_CACHE))
        _results = json.loads(RESULTS_CACHE.read_text())
    return _results


def get_model(key: str) -> dict:
    return get_results()["models"][key]


def best_model_key() -> str:
    return get_results()["best_model_key"]


def ordered_models():
    results = get_results()
    return [(k, results["models"][k]) for k in MODEL_ORDER if k in results["models"]]
