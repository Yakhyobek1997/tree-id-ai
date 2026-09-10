"""Evaluate expert-labelled, held-out tree observations from JSONL.

Usage: python -m backend.analysis.evaluation dataset.jsonl --output report.json
No network calls. Predictions must come from the frozen production pipeline.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path


def wilson_interval(correct, total):
    if not total:
        return [None, None]
    z = 1.959963984540054
    p = correct / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0, center - radius), min(1, center + radius)]


def evaluate(records, target=0.98):
    """Count abstentions as errors; prevent same-tree/image leakage across splits."""
    if not 0 < target < 1:
        raise ValueError("Target must be between 0 and 1")
    groups, hashes, samples, observations = {}, {}, set(), set()
    tests = defaultdict(list)
    for row in records:
        for key in ("sample_id", "tree_id", "split", "task", "truth"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"Missing or invalid {key}")
        if row["split"] not in {"train", "validation", "test"}:
            raise ValueError("Invalid split")
        if row["task"] not in {"species", "disease"}:
            raise ValueError("Evaluate species and disease separately; age requires regression metrics")
        sample_key = (row["task"], row["sample_id"])
        if sample_key in samples:
            raise ValueError("Duplicate sample in the same task")
        samples.add(sample_key)
        old_split = groups.setdefault(row["tree_id"], row["split"])
        if old_split != row["split"]:
            raise ValueError("Tree leakage between training, validation and test")
        image_hashes = row.get("image_sha256")
        if not isinstance(image_hashes, list) or not image_hashes:
            raise ValueError("image_sha256 must list all image hashes in the observation")
        for digest in image_hashes:
            if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError("Invalid image SHA256")
            old = hashes.setdefault(digest, (row["split"], row["tree_id"]))
            if old != (row["split"], row["tree_id"]):
                raise ValueError("Image leakage or conflicting tree identity")
        if row["split"] != "test":
            continue
        observation_key = (row["task"], row["tree_id"])
        if observation_key in observations:
            raise ValueError("Test set requires one independent observation per tree per task")
        observations.add(observation_key)
        for key in ("provider", "model_version", "pipeline_version", "scope", "label_source"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"Test rows require {key}")
        predicted = row.get("prediction")
        if predicted is not None and (not isinstance(predicted, str) or not predicted.strip()):
            raise ValueError("prediction must be a label or null for abstention")
        tests[row["task"]].append(row)
    if not tests:
        raise ValueError("No independent test observations")
    results = {}
    for task, rows in tests.items():
        identities = {(r["provider"], r["model_version"], r["pipeline_version"], r["scope"]) for r in rows}
        if len(identities) != 1:
            raise ValueError("Do not mix provider/model/pipeline versions or scopes in one task")
        labels = sorted({r["truth"] for r in rows} | {r["prediction"] for r in rows if r["prediction"] is not None})
        correct = sum(r["prediction"] == r["truth"] for r in rows)
        accepted = sum(r["prediction"] is not None for r in rows)
        per_class = {}
        confusion = defaultdict(Counter)
        for row in rows:
            confusion[row["truth"]][row["prediction"] if row["prediction"] is not None else "__abstain__"] += 1
        for label in labels:
            tp = sum(r["truth"] == label and r["prediction"] == label for r in rows)
            support = sum(r["truth"] == label for r in rows)
            predicted_count = sum(r["prediction"] == label for r in rows)
            precision = tp / predicted_count if predicted_count else 0
            recall = tp / support if support else 0
            per_class[label] = {"support": support, "precision": precision, "recall": recall,
                                "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0}
        interval = wilson_interval(correct, len(rows))
        provider, version, pipeline, scope = next(iter(identities))
        results[task] = {
            "provider": provider, "model_version": version, "pipeline_version": pipeline, "scope": scope,
            "test_trees": len(rows), "correct": correct, "abstentions": len(rows) - accepted,
            "accuracy": correct / len(rows), "accuracy_ci95": interval,
            "coverage": accepted / len(rows),
            "accepted_accuracy": correct / accepted if accepted else None,
            "macro_f1": sum(item["f1"] for item in per_class.values()) / len(per_class),
            "per_class": per_class, "confusion_matrix": {key: dict(value) for key, value in confusion.items()},
            "target": target,
            "target_supported_on_test_set": len(rows) >= 200 and interval[0] >= target,
            "gate": "At least 200 independent trees and Wilson 95% lower bound >= target",
        }
    return {"created_at": datetime.now(timezone.utc).isoformat(), "tasks": results,
            "limitations": ["Labels and test-set representativeness require independent expert review.",
                            "Checks cannot establish absence from an external provider's pretraining data.",
                            "Results apply only to the stated scope and frozen model/pipeline.",
                            "Near-duplicates with different pixels require a separate dataset audit."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.dataset.resolve() == args.output.resolve():
        parser.error("Output must not overwrite the source dataset")
    try:
        content = args.dataset.read_bytes()
        records = [json.loads(line) for line in content.decode("utf-8-sig").splitlines() if line.strip()]
        report = evaluate(records)
        report["dataset_sha256"] = hashlib.sha256(content).hexdigest()
    except (ValueError, TypeError, KeyError, OSError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
