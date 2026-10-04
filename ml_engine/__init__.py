"""Dataset Doctor's framework-independent dataset analysis engine."""

from .core.result import AnalysisResult, Finding
from .scoring.health_score import HealthScoreConfig, calculate_health_score


def analyze_tabular(data, target_column=None):
    """Analyze tabular data, importing optional pandas dependencies on demand."""
    from .tabular.analyzer import analyze_tabular as _analyze_tabular

    return _analyze_tabular(data, target_column=target_column)


def analyze_image_dataset(source, **options):
    """Analyze image files, importing the image stack on demand."""
    from .image.analyzer import analyze_image_dataset as _analyze_image_dataset

    return _analyze_image_dataset(source, **options)


def analyze_text_dataset(source, **options):
    """Analyze a text corpus, importing text helpers on demand."""
    from .text.analyzer import analyze_text_dataset as _analyze_text_dataset

    return _analyze_text_dataset(source, **options)


__all__ = ["AnalysisResult", "Finding", "HealthScoreConfig", "analyze_image_dataset", "analyze_tabular", "analyze_text_dataset", "calculate_health_score"]
