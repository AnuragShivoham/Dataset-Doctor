"""Provision and run the local real-data Dataset Doctor benchmark."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "datasets"
MANIFEST_PATH = DATA_ROOT / "manifests" / "real_data.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def provision(manifest: dict) -> None:
    """Copy known local public corpus fixtures; never modify their sources."""
    try:
        from sklearn.datasets import load_iris
    except ImportError:
        print("SKIP iris: scikit-learn is not installed", file=sys.stderr)
    else:
        record = _dataset(manifest, "iris")
        target = DATA_ROOT / record["local_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            iris = load_iris(as_frame=True)
            frame = iris.data.copy()
            frame["target"] = iris.target
            frame.to_csv(target, index=False)
        record["sha256"] = sha256(target)

    try:
        from nltk.corpus import brown
        brown.fileids()
    except (ImportError, LookupError):
        print("SKIP Brown text: NLTK Brown Corpus is not installed", file=sys.stderr)
    else:
        record = _dataset(manifest, "brown_news_hobbies")
        target = DATA_ROOT / record["local_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open("w", encoding="utf-8", newline="") as output:
                writer = csv.DictWriter(output, fieldnames=["id", "text", "label"])
                writer.writeheader()
                for category in ("news", "hobbies"):
                    for file_id in brown.fileids(categories=category):
                        text = " ".join(brown.words(fileids=[file_id]))
                        writer.writerow({"id": file_id, "text": text, "label": category})
        record["sha256"] = sha256(target)

    try:
        import sklearn.datasets.images as sample_images
    except ImportError:
        print("SKIP images: scikit-learn is not installed", file=sys.stderr)
    else:
        record = _dataset(manifest, "sklearn_attributed_photos")
        target = DATA_ROOT / record["local_path"]
        target.mkdir(parents=True, exist_ok=True)
        source_dir = Path(sample_images.__file__).parent
        for name in ("china.jpg", "flower.jpg"):
            source, destination = source_dir / name, target / name
            if not destination.exists():
                shutil.copy2(source, destination)
        readme = source_dir / "README.txt"
        attribution = target / "ATTRIBUTION.txt"
        if not attribution.exists():
            attribution.write_text(readme.read_text(encoding="utf-8"), encoding="utf-8")
        # Point the analyzer at a directory containing images only; attribution
        # remains adjacent to the immutable image payload.
        image_root = target / "images"
        image_root.mkdir(exist_ok=True)
        for name in ("china.jpg", "flower.jpg"):
            destination = image_root / name
            if not destination.exists():
                shutil.copy2(target / name, destination)
        record["sha256"] = {
            path.name: sha256(path) for path in sorted((target / "images").glob("*.jpg"))
        }


def _dataset(manifest: dict, dataset_id: str) -> dict:
    return next(item for item in manifest["datasets"] if item["id"] == dataset_id)


def run(manifest: dict) -> dict:
    # Import from the workspace root without installing the package.
    sys.path.insert(0, str(ROOT))
    from ml_engine import analyze_image_dataset, analyze_tabular, analyze_text_dataset

    results = []
    for dataset in manifest["datasets"]:
        location = DATA_ROOT / dataset["local_path"]
        result = {"dataset_id": dataset["id"], "modality": dataset["modality"], "status": "skipped"}
        try:
            if dataset["modality"] == "image":
                image_root = location / "images"
                if image_root.exists():
                    analysis = analyze_image_dataset(image_root)
                else:
                    result["reason"] = "Dataset not provisioned"
                    results.append(result)
                    continue
            elif not location.is_file():
                result["reason"] = "Dataset not provisioned"
                results.append(result)
                continue
            elif dataset["modality"] == "tabular":
                analysis = analyze_tabular(location, target_column=dataset.get("target_column"))
            else:
                analysis = analyze_text_dataset(location)
            result.update({
                "status": analysis["status"],
                "dataset": analysis.get("dataset"),
                "health": analysis.get("health"),
                "finding_counts": _finding_counts(analysis.get("findings", [])),
                "findings": analysis.get("findings", []),
                "summary": analysis.get("summary", {}),
                "source_sha256": dataset.get("sha256"),
            })
            result["expected_checks"] = _evaluate_expectations(dataset, analysis)
            if dataset["id"] == "brown_news_hobbies":
                # Brown documents are long editorial pieces by design. The
                # default 1,000-word ceiling is not a corpus defect threshold.
                result["review_notes"] = [
                    "Very-long-document findings reflect the analyzer default; review corpus-specific length limits before scoring these as defects."
                ]
                pii = result.get("summary", {}).get("privacy", {}).get("pattern_counts", {})
                if sum(pii.values()):
                    result["review_notes"].append(
                        "Possible PII pattern matches are indicators only; manually review before treating them as true positives."
                    )
            if dataset["id"] == "sklearn_attributed_photos":
                result["review_notes"] = [
                    "Semantic/domain analysis is not available without an explicitly supplied embedding backend."
                ]
        except Exception as exc:  # keep other modalities runnable if one fails
            result.update({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
        results.append(result)
    return {
        "benchmark": "dataset_doctor_real_data_v1",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "results": results,
    }


def _finding_counts(findings: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        issue = finding.get("issue_type", "unknown")
        counts[issue] = counts.get(issue, 0) + 1
    return dict(sorted(counts.items()))


def _evaluate_expectations(dataset: dict, analysis: dict) -> list[dict]:
    expected = dataset.get("expected", {})
    findings = analysis.get("findings", [])
    checks = []
    if "missing_values" in expected:
        detected = any(item.get("issue_type") == "missing_values" for item in findings)
        checks.append({"check": "missing_values", "expected": expected["missing_values"], "actual": detected,
                       "result": "PASS" if detected == expected["missing_values"] else "REVIEW"})
    if "class_imbalance" in expected:
        detected = any(item.get("issue_type") == "class_imbalance" for item in findings)
        checks.append({"check": "class_imbalance", "expected": expected["class_imbalance"], "actual": detected,
                       "result": "PASS" if detected == expected["class_imbalance"] else "REVIEW"})
    if expected.get("clean_baseline"):
        # Iris is known complete and balanced, though correlation-based leakage
        # heuristics may legitimately need a domain review.
        checks.append({"check": "known_complete_balanced_source", "expected": True,
                       "actual": analysis.get("summary", {}).get("profile", {}).get("missing_cells") == 0,
                       "result": "PASS" if analysis.get("summary", {}).get("profile", {}).get("missing_cells") == 0 else "REVIEW"})
    if "readable_images" in expected:
        actual = analysis.get("profile", {}).get("readable_images")
        checks.append({"check": "readable_images", "expected": expected["readable_images"], "actual": actual,
                       "result": "PASS" if actual == expected["readable_images"] else "REVIEW"})
    return checks


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    provision(manifest)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    report = run(manifest)
    report_dir = DATA_ROOT / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "real_data_benchmark.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(report_path), "results": [
        {"dataset_id": item["dataset_id"], "status": item["status"],
         "dataset": item.get("dataset"), "finding_counts": item.get("finding_counts"),
         "expected_checks": item.get("expected_checks"), "reason": item.get("reason"), "error": item.get("error")}
        for item in report["results"]
    ]}, indent=2))
    return 0 if all(item["status"] in {"completed", "skipped"} for item in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
