# Multi-view tree analysis

The `/scan` screen accepts up to five views of one tree and returns image-quality,
species, disease-candidate and planting-record results. Existing registration and
same-tree retrieval are available at `/register` and `/identify`.

This implementation has **not demonstrated 98% diagnostic accuracy**. No expert
field benchmark or live provider credential was supplied. Software tests use
synthetic images and mocked responses, and do not measure biological accuracy.

## Setup

Install the backend requirements in the project's Python environment. The added
dependency is `requests>=2.32.0,<3`. Add to `tree-recognition-system/.env`:

```dotenv
PLANTNET_API_KEY=your_private_key
PLANTNET_PROJECT=all
PLANTNET_TIMEOUT=30
ANALYSIS_MIN_SCORE=0.80
ANALYSIS_MIN_MARGIN=0.15
API_PORT=8000
```

Keep the key on the backend only. Without a key, image-quality checks and time
since planting work; the UI clearly marks species/health inference unavailable.
Start `python backend/run_server.py` from the project and `npm.cmd run dev` from
`frontend`. Visit `http://localhost:5173/scan`. The frontend uses Vite's `/api`
proxy to port 8000; deployments need an equivalent proxy or `VITE_API_URL`.

The integration follows the official [species API](https://my.plantnet.org/doc/api/identify)
and [disease API](https://my.plantnet.org/doc/api/diseases). Disease coverage is
limited to supported species/pathologies. A negative or empty prediction never
means the tree is healthy. Species and disease requests are independent and may
consume two provider credits per scan. Images are sent only with explicit consent.
EXIF/GPS metadata is removed; remote retention follows the provider's policies.

## Behavior and API

- JPEG, PNG and WebP decoding; 1–5 files, 10 MB/file, 24 MP/image. Total request
  limit defaults to 52 MiB including multipart overhead.
- Orientation correction, metadata-free JPEG preparation and bounded resolution.
- Exposure, contrast, sharpness and resolution checks; duplicate decoded-pixel
  hashes. Quality thresholds are heuristics, not a trained tree detector.
- Ranked candidates, provider model version, score and margin based abstention.
  Scores are uncalibrated model outputs, not measured accuracy.
- Time since planting and user-supplied diameter/height. Biological age and
  young/mature/old stage remain unknown until there is sufficient validated data.
- JSON reports persist in `data/database/analyses.sqlite3` and can be downloaded.
  This new endpoint stores metadata/hashes/results, not uploaded image pixels.

`GET /api/analysis/capabilities` returns configuration and accuracy status.

`POST /api/analyze-tree` takes multipart `images` repeated 1–5 times, `organs`
in matching order (`auto`, `leaf`, `bark`, `flower`, `fruit`), and optional
`planted_date` (ISO date), `dbh_cm`, `height_m`. Set `external_consent=true` to
permit remote analysis. Legacy single `image` is accepted too.

Response: `{ "success": true, "report": {...} }`. Check report and task statuses:
HTTP 200 does not imply a confident diagnosis. Missing setup/consent, bad image
quality, provider failures and partial results are explicit. Invalid uploads use
400; oversize requests use 413. API credentials are redacted from errors.

`GET /api/analysis/<report-id>` returns the stored report or 404. This project
still has no per-user report authorization: add ownership/authentication, rate
limits, retention/deletion and production serving before public deployment.

## The 98% acceptance target

Species and disease require separate expert-labelled benchmarks. Tree identity
requires a retrieval benchmark; numerical age needs age labels and error/range
metrics. A single universal percentage is not appropriate for these different tasks.

Create JSONL records from predictions produced by the frozen pipeline:

```json
{"sample_id":"obs-001","tree_id":"tree-001","split":"test","task":"species","truth":"Quercus robur","prediction":null,"image_sha256":["0000000000000000000000000000000000000000000000000000000000000000"],"provider":"plantnet","model_version":"actual-version","pipeline_version":"tree-analysis-1.0","scope":"chosen-region-and-species","label_source":"expert-review-reference"}
```

The example is a schema illustration, not a genuine evaluation observation.
Use all decoded-image hashes from `report.quality`, and the returned species or
health `label` as prediction. Preserve null abstentions and quality/API failures;
do not exclude difficult observations. Include training and validation records
when those splits exist. Never tune thresholds using the final test set.

```powershell
python -m backend.analysis.evaluation field-evaluation.jsonl --output evaluation-report.json
```

The evaluator checks cross-split physical-tree/image leakage, repeated test-tree
observations and mixed model versions/scopes. It counts abstentions as errors in
overall accuracy, and reports coverage, accepted-only accuracy, macro F1,
per-class precision/recall and a confusion matrix. The acceptance gate requires
200+ independent trees and a Wilson 95% lower confidence bound of at least 98%.
A point estimate of 98% alone does not pass. Class/site/season results and dataset
representativeness still require expert review. Near-duplicates, label quality and
presence in provider pretraining cannot be verified by this script.

The UI remains “not evaluated” until a reviewed field benchmark is tied to the
actual deployed model version and scope. An exported metrics file does not
automatically become a deployment certification.

## Remaining model work

The local datasets in `data/datasets` are for collection and development. Merely
copying images into folders does not train a model or improve the remote provider.
Next define a region/species scope, verify taxonomic and health labels, group all
views of each physical tree and train/validate local models. DINOv3 is one current
backbone option in [Hugging Face's documentation](https://huggingface.co/docs/transformers/model_doc/dinov3);
no DINOv3 training, segmentation model or biological-age model is claimed here.

## Verification

```powershell
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

From `frontend`, run `npm.cmd run build`. Live provider validation requires a key
and authorized images. Synthetic/mock tests verify behavior only.
