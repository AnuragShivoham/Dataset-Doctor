# Dataset Doctor tabular API contract

The backend integration entry point is `ml_engine.analyze_tabular`. API code
should call this function instead of importing individual analyzers.

```python
from ml_engine import analyze_tabular

result = analyze_tabular("path/to/dataset.csv", target_column="label")
```

`target_column` is optional. When supplied, the engine reports class
distribution and checks for unusually strong feature-to-target relationships.
The engine is diagnostic only and does not mutate or clean the input dataset.

For image files, `ml_engine.analyze_image_dataset(path)` provides a parallel
read-only analysis for a single image or a directory tree. It supports JPG,
JPEG, PNG, and WebP; directory class labels are inferred from the first
subfolder under the supplied root.

Image semantic checks are opt-in. Supply `expected_domain`, optional
`class_descriptions`, and a `semantic_backend` implementing `embed_images(paths)`
and `embed_texts(prompts)`. The engine compares normalized embeddings by cosine
similarity and reports low-similarity cases for manual review. It does not
download a model, infer a definitive class, or report similarity as calibrated
confidence. Without a backend, semantic status is `unavailable`; with no
semantic expectations supplied, it is `not_requested`.

The JSON-ready mapping contains:

- `status`: `completed` when analysis succeeds.
- `dataset`: row and column counts.
- `profile`: dataset-level profile fields.
- `health`: overall score, application grade, component scores, and weights.
- `findings`: standardized issue records with analyzer, issue type, severity,
  message, score impact, column, and metadata.
- `recommendations`: prioritized action records with category, issue type,
  optional column, and action text.
- `summary`: detailed profile and analyzer outputs. This remains available for
  existing callers as the top-level contract is adopted.

Health grades are application labels: Excellent (90–100), Good (75–89), Fair
(60–74), Poor (40–59), and Critical (0–39). Component weights are configurable
through `HealthScoreConfig`.
