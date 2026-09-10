"""Download three complete small BarkNet species archives, with tree IDs and DBH.

Source: https://zenodo.org/records/11508014 (MIT license in record metadata).
Default archives total about 283 MB; the complete BarkNet collection is 32.3 GB.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path, PurePosixPath
import re
import zipfile

from PIL import Image
import requests

from .download_public import ROOT, slug


RECORD = "https://zenodo.org/api/records/11508014"
SPECIES = {"ERB": "Acer platanoides", "PEG": "Populus grandidentata", "PID": "Pinus rigida"}


def download_file(file, destination):
    expected = file["checksum"]
    if not expected.startswith("md5:"):
        raise ValueError("Expected publisher MD5 checksum")
    if destination.exists():
        if hashlib.md5(destination.read_bytes()).hexdigest() == expected.split(":", 1)[1]:
            return
        raise ValueError("Existing archive checksum mismatch; review instead of overwriting")
    temporary = destination.with_suffix(destination.suffix + ".part")
    if temporary.exists():
        raise ValueError(f"Previous partial download exists: {temporary.name}; review before retrying")
    digest, total = hashlib.md5(), 0
    with requests.get(file["links"]["self"], timeout=(15, 60), stream=True) as response:
        response.raise_for_status()
        with temporary.open("xb") as output:
            for chunk in response.iter_content(1024 * 1024):
                total += len(chunk)
                if total > file["size"]:
                    raise ValueError("Download exceeds published archive size")
                digest.update(chunk)
                output.write(chunk)
    if total != file["size"] or digest.hexdigest() != expected.split(":", 1)[1]:
        raise ValueError("Downloaded archive failed publisher checksum/size verification")
    temporary.rename(destination)


def import_archive(path, root, code):
    rows = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            name = PurePosixPath(member.filename).name
            if member.is_dir() or name.startswith(".") or PurePosixPath(name).suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                continue
            match = re.match(r"^(\d+)_([A-Z]{3})_([0-9.]+)_", name)
            if not match or match[2] != code:
                raise ValueError(f"Unknown BarkNet filename schema: {name}")
            if member.file_size > 15 * 1024 * 1024:
                raise ValueError("Archive member exceeds image size limit")
            content = archive.read(member)
            with Image.open(BytesIO(content)) as image:
                if image.width * image.height > 24_000_000:
                    raise ValueError("Decoded image exceeds 24 MP")
                image.verify()
            digest = hashlib.sha256(content).hexdigest()
            destination = root / "images" / "bark" / slug(SPECIES[code]) / f"barknet_{digest[:24]}.jpg"
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
                    raise ValueError("Existing image differs; refusing overwrite")
            else:
                with destination.open("xb") as output:
                    output.write(content)
            circumference = float(match[3])
            rows.append({
                "sample_id": f"barknet-{digest[:24]}", "path": destination.relative_to(root).as_posix(),
                "organ": "bark", "species_label": SPECIES[code], "taxon_verified": False,
                "tree_id": f"barknet-{match[1]}", "circumference_cm": circumference,
                "dbh_cm": round(circumference / math.pi, 3),
                "disease": None, "biological_age_years": None,
                "split": "unassigned", "source_split": None, "label_source": "publisher_filename_and_readme",
                "sha256": digest, "source_path": member.filename,
                "source_url": "https://zenodo.org/records/11508014", "license": "MIT",
                "source_version": "11508014", "downloaded_at": datetime.now(timezone.utc).isoformat(),
                "bytes": len(content),
            })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--species", nargs="+", choices=list(SPECIES), default=list(SPECIES))
    args = parser.parse_args()
    source_dir = ROOT / "sources" / "barknet"
    source_dir.mkdir(parents=True, exist_ok=True)
    (ROOT / "manifests").mkdir(parents=True, exist_ok=True)
    response = requests.get(RECORD, timeout=(15, 60))
    response.raise_for_status()
    record = response.json()
    if record["metadata"].get("license", {}).get("id") != "mit-license":
        raise ValueError("Dataset license changed; review required")
    (source_dir / "metadata.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    files = {item["key"]: item for item in record["files"]}
    download_file(files["README.md"], source_dir / "README.source.md")
    for code in args.species:
        item = files[f"{code}.zip"]
        if item["size"] > 110_000_000:
            raise ValueError("Archive exceeds expected starter size")
        print(f"Downloading {code}: {item['size'] / 1024**2:.1f} MB", flush=True)
        archive = source_dir / f"{code}.zip"
        download_file(item, archive)
        rows = import_archive(archive, ROOT, code)
        # One deterministic manifest per archive; images and source archives are retained.
        output = ROOT / "manifests" / f"barknet_{code}.jsonl"
        output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        print(f"{code}: {len(rows)} images, {len({row['tree_id'] for row in rows})} trees", flush=True)


if __name__ == "__main__":
    main()
