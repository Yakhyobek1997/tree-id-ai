"""Reproducible public-data importer. Default: 3 images/class/organ from Urban Street.

Run from the project: python -m backend.datasets.download_public
Use --per-class 10 for a larger development collection. No authentication needed
for public downloads; login-gated responses are reported, never bypassed.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import time
from urllib.parse import quote
import zipfile

from PIL import Image
import requests


ROOT = Path(__file__).resolve().parents[2] / "data" / "datasets"
OWNER = "erickendric"
BASE = "https://www.kaggle.com/api/v1/datasets"
ORGANS = {"branch": "branch", "bark": "trunk", "leaf": "leaf", "whole_tree": "tree"}
ALLOWED_LICENSES = {"GNU Lesser General Public License 3.0", "CC0: Public Domain",
                    "CC BY-SA 4.0", "CC BY 4.0", "MIT"}
MAX_IMAGE_BYTES = 15 * 1024 * 1024


def slug(value):
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("._") or "unknown"


def read_json(url, params=None):
    response = requests.get(url, params=params, timeout=(10, 45))
    response.raise_for_status()
    return response.json()


def list_files(dataset):
    result, token, seen_tokens = [], None, set()
    while True:
        params = {"pageSize": 1000}
        if token:
            params["pageToken"] = token
        body = read_json(f"{BASE}/list/{OWNER}/{dataset}", params)
        if body.get("errorMessage"):
            raise ValueError(body["errorMessage"])
        result.extend(body.get("datasetFiles", []))
        token = body.get("nextPageToken")
        if not token:
            return result
        if token in seen_tokens:
            raise ValueError("Dataset pagination repeated; refusing incomplete index")
        seen_tokens.add(token)


def get_image(url):
    with requests.get(url, timeout=(10, 60), stream=True) as response:
        response.raise_for_status()
        content = bytearray()
        for chunk in response.iter_content(64 * 1024):
            content.extend(chunk)
            if len(content) > MAX_IMAGE_BYTES:
                raise ValueError("Individual download exceeds 15 MB")
    content = bytes(content)
    if content.startswith(b"PK"):
        with zipfile.ZipFile(BytesIO(content)) as archive:
            images = [info for info in archive.infolist() if not info.is_dir()
                      and PurePosixPath(info.filename).suffix.lower() in {".jpg", ".jpeg", ".png"}]
            if len(images) != 1 or images[0].file_size > MAX_IMAGE_BYTES:
                raise ValueError("Expected exactly one bounded image in download")
            content = archive.read(images[0])
    with Image.open(BytesIO(content)) as image:
        if image.width * image.height > 24_000_000:
            raise ValueError("Decoded image exceeds 24 MP")
        image.verify()
    return content


def import_urban(root, organ, per_class, max_mb):
    source_organ = ORGANS[organ]
    dataset = f"tree-dataset-of-urban-street-classification-{source_organ}"
    source_dir = root / "sources" / f"urban_{organ}"
    source_dir.mkdir(parents=True, exist_ok=True)
    metadata = read_json(f"{BASE}/view/{OWNER}/{dataset}")
    license_name = metadata.get("licenseName")
    if license_name not in ALLOWED_LICENSES:
        raise ValueError(f"License needs review: {license_name}")
    (source_dir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    files = list_files(dataset)
    (source_dir / "file_index.json").write_text(json.dumps(files, ensure_ascii=False), encoding="utf-8")
    # Prefer development/train images, but preserve the original split verbatim.
    files.sort(key=lambda row: ("/train/" not in row["name"].lower(), row["name"]))
    counts = Counter()
    manifest_path = root / "manifests" / f"urban_{organ}.jsonl"
    existing = {}
    if manifest_path.exists():
        existing = {row["source_path"]: row for row in
                    (json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line)}
    downloaded_bytes, failures = 0, []
    for item in files:
        name = item["name"]
        parts = PurePosixPath(name).parts
        if len(parts) < 4 or PurePosixPath(name).suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        label = parts[-2]
        if counts[label] >= per_class:
            continue
        if item.get("totalBytes", 0) > MAX_IMAGE_BYTES:
            continue
        old = existing.get(name)
        if old:
            local = (root / old["path"]).resolve()
            if not local.is_relative_to(root.resolve()):
                raise ValueError("Manifest path leaves the dataset directory")
            if local.is_file() and hashlib.sha256(local.read_bytes()).hexdigest() == old["sha256"]:
                counts[label] += 1
                continue
            raise ValueError(f"Existing dataset file missing/changed: {old['path']}; review before reimport")
        if downloaded_bytes + item.get("totalBytes", MAX_IMAGE_BYTES) > max_mb * 1024 * 1024:
            print(f"{organ}: download budget reached", flush=True)
            break
        url = f"{BASE}/download/{OWNER}/{dataset}/{quote(name, safe='')}"
        try:
            content = get_image(url)
        except (requests.RequestException, ValueError, OSError, zipfile.BadZipFile) as exc:
            failures.append({"source_path": name, "error": type(exc).__name__})
            print(f"{organ}: skipped {slug(label)} ({type(exc).__name__})", flush=True)
            if len(failures) >= 5:
                break
            continue
        digest = hashlib.sha256(content).hexdigest()
        destination = root / "images" / organ / slug(label) / f"{digest[:24]}.jpg"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and destination.read_bytes() != content:
            raise ValueError("Refusing to overwrite an existing file with different data")
        if not destination.exists():
            with destination.open("xb") as output:
                output.write(content)
        row = {
            "sample_id": f"urban-{organ}-{digest[:24]}", "path": destination.relative_to(root).as_posix(),
            "organ": organ, "species_label": label, "taxon_verified": False,
            "tree_id": None, "disease": None, "biological_age_years": None,
            "source_split": parts[-3], "split": "unassigned", "label_source": "publisher_folder",
            "sha256": digest, "source_path": name, "source_url": f"https://www.kaggle.com/datasets/{OWNER}/{dataset}",
            "license": license_name, "source_version": metadata.get("currentVersionNumber"),
            "downloaded_at": datetime.now(timezone.utc).isoformat(), "bytes": len(content),
        }
        with manifest_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
        existing[name] = row
        counts[label] += 1
        downloaded_bytes += len(content)
        if sum(counts.values()) % 10 == 0:
            print(f"{organ}: {sum(counts.values())} images, {downloaded_bytes / 1024**2:.1f} MB downloaded", flush=True)
        time.sleep(0.15)
    report = {"organ": organ, "images_in_selection": sum(counts.values()), "classes": dict(counts),
              "downloaded_bytes": downloaded_bytes, "failures": failures,
              "source_index_images": len(files), "per_class_requested": per_class}
    (source_dir / "import_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "classes"}), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--organs", nargs="+", choices=list(ORGANS), default=list(ORGANS))
    parser.add_argument("--per-class", type=int, default=3)
    parser.add_argument("--max-mb-per-organ", type=int, default=250)
    args = parser.parse_args()
    if not 1 <= args.per_class <= 10000 or not 1 <= args.max_mb_per_organ <= 50000:
        parser.error("Positive bounded counts are required")
    for folder in ("manifests", "sources", "images/branch", "images/bark", "images/leaf",
                   "images/whole_tree", "images/disease", "images/roots", "annotations", "splits"):
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    organs = list(dict.fromkeys(args.organs))
    with ThreadPoolExecutor(max_workers=min(4, len(organs))) as pool:
        tasks = [pool.submit(import_urban, ROOT, organ, args.per_class, args.max_mb_per_organ)
                 for organ in organs]
        for task in tasks:
            task.result()


if __name__ == "__main__":
    main()
