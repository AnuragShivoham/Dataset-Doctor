# Local real-data benchmark

Run from the project root with `python scripts/run_real_data_benchmark.py` (or
`.\venv\Scripts\python.exe scripts\run_real_data_benchmark.py` on Windows).
Dataset payloads live under this directory and are ignored by Git; only
manifests, benchmark code, and generated reports are intended to be tracked.
The runner never changes source dataset files. Reports are written to
`datasets/reports/real_data_benchmark.json`.

Provision files only from the sources and licenses documented in the
manifests. Keep the recorded SHA-256 values current when replacing a source
file. Image semantic findings remain unavailable unless a caller supplies an
explicit embedding backend; scores are heuristics requiring human review.
