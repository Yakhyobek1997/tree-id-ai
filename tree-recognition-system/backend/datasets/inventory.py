"""Validate downloaded image manifests and write a local inventory summary."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from PIL import Image

from .download_public import ROOT


def load_records(root=ROOT):
    root = Path(root).resolve()
    records = []
    for manifest in sorted((root / "manifests").glob("*.jsonl")):
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            path = (root / row["path"]).resolve()
            if not path.is_relative_to(root):
                raise ValueError("Manifest image path leaves dataset directory")
            records.append(row)
    return records


def summarize(root=ROOT, verify=False):
    root = Path(root)
    records = load_records(root)
    counts = Counter()
    classes = defaultdict(set)
    hashes = Counter()
    errors = []
    for row in records:
        path = root / row["path"]
        if not path.is_file():
            errors.append({"path": row["path"], "error": "missing"})
            continue
        if verify:
            try:
                if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                    raise ValueError("SHA256 mismatch")
                with Image.open(path) as image:
                    image.verify()
            except (ValueError, OSError) as exc:
                errors.append({"path": row["path"], "error": str(exc)})
                continue
        counts[row["organ"]] += 1
        classes[row["organ"]].add(row["species_label"])
        hashes[row["sha256"]] += 1
    return {
        "total_images": sum(counts.values()), "images_by_organ": dict(counts),
        "class_count_by_organ": {key: len(value) for key, value in classes.items()},
        "classes_by_organ": {key: sorted(value) for key, value in classes.items()},
        "known_physical_trees": len({r["tree_id"] for r in records if r.get("tree_id")}),
        "images_without_tree_id": sum(not r.get("tree_id") for r in records),
        "disease_labelled_images": sum(r.get("disease") is not None for r in records),
        "age_labelled_images": sum(r.get("biological_age_years") is not None for r in records),
        "duplicate_hashes": sum(count - 1 for count in hashes.values()),
        "image_bytes": sum(r["bytes"] for r in records), "errors": errors,
        "trained_model": False, "field_accuracy": None,
    }


class TreeImageDataset:
    """PIL dataset compatible with DataLoader after a tensor transform is supplied.

    Training callers must explicitly choose curated records/splits. Publisher
    samples are unassigned and independently unverified by default.
    """
    def __init__(self, records, root=ROOT, transform=None):
        self.root = Path(root).resolve()
        self.records = list(records)
        self.transform = transform
        self.labels = sorted({row["species_label"] for row in self.records})
        self.label_to_id = {label: i for i, label in enumerate(self.labels)}

    def __len__(self):
        return len(self.records)

    def __getitem__(self, index):
        row = self.records[index]
        path = (self.root / row["path"]).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError("Image path leaves dataset directory")
        with Image.open(path) as image:
            image = image.convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, self.label_to_id[row["species_label"]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    summary = summarize(verify=args.verify)
    (ROOT / "inventory.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "classes_by_organ"}, indent=2))
    if summary["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
