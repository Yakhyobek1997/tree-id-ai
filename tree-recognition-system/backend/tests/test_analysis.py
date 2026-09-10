"""Offline contract/regression tests. Synthetic images do not measure AI accuracy."""
from copy import deepcopy
from datetime import date
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

import numpy as np
from PIL import Image
import requests
from flask import Flask

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis.evaluation import evaluate
from analysis.images import prepare_image
from analysis.provider import PlantNetProvider, ProviderError
from analysis.service import AnalysisService, age_result, validate_context
from analysis.store import AnalysisStore
from api.analysis_routes import create_analysis_blueprint


def image_bytes(kind="noise", size=(850, 850)):
    values = np.random.default_rng(42).integers(35, 220, (*size, 3), dtype=np.uint8)
    if kind == "blank":
        values[:] = 255
    output = BytesIO()
    Image.fromarray(values).save(output, format="PNG")
    return output.getvalue()


def provider_payload(task="species", score=0.96):
    if task == "species":
        row = {"score": score, "species": {"scientificNameWithoutAuthor": "Quercus robur", "commonNames": ["Oak"]}}
    else:
        row = {"score": score, "name": "APHISP", "description": "Aphis sp."}
    return {"results": [row], "version": "test-model-v1"}


class FakeProvider:
    name = "test-provider"
    configured = True

    def __init__(self, candidates=None):
        self.calls = []
        self.candidates = candidates if candidates is not None else [{"label": "oak", "score": 0.99}]

    def predict(self, task, images):
        self.calls.append((task, len(images)))
        return {"candidates": self.candidates, "model_version": "fixture-v1"}


class QualityTests(unittest.TestCase):
    def test_decodes_checks_and_removes_metadata(self):
        prepared = prepare_image(image_bytes(), "leaf")
        self.assertEqual(prepared.quality["status"], "accepted")
        with Image.open(BytesIO(prepared.content)) as img:
            self.assertEqual(img.format, "JPEG")
            self.assertEqual(len(img.getexif()), 0)

    def test_low_quality_rejected(self):
        self.assertEqual(prepare_image(image_bytes("blank"), "auto").quality["status"], "rejected")
        self.assertEqual(prepare_image(image_bytes(size=(100, 100)), "leaf").quality["status"], "rejected")

    def test_invalid_file_and_organ(self):
        for data, organ in ((b"not an image", "auto"), (image_bytes(), "root")):
            with self.subTest(organ=organ), self.assertRaises(ValueError):
                prepare_image(data, organ)


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.http = Mock()
        self.response = self.http.post.return_value
        self.response.status_code = 200
        self.provider = PlantNetProvider("private-test-key", http=self.http)
        self.images = [prepare_image(image_bytes(), "leaf")]

    def test_official_species_and_disease_contract(self):
        for task, label in (("species", "Quercus robur"), ("disease", "APHISP")):
            with self.subTest(task=task):
                self.response.json.return_value = provider_payload(task)
                result = self.provider.predict(task, self.images)
                self.assertEqual(result["candidates"][0]["label"], label)
                kwargs = self.http.post.call_args.kwargs
                self.assertEqual(kwargs["data"], [("organs", "leaf")])
                self.assertEqual(kwargs["files"][0][0], "images")
                self.assertFalse(kwargs["allow_redirects"])
                self.assertNotIn("no-reject", kwargs["params"])

    def test_rejections_do_not_mean_healthy(self):
        self.response.status_code = 404
        self.assertEqual(self.provider.predict("disease", self.images)["candidates"], [])

    def test_quota_and_auth_failures(self):
        for status, reason in ((429, "quota_exceeded"), (401, "unauthorized"), (503, "unavailable")):
            self.response.status_code = status
            with self.assertRaises(ProviderError) as caught:
                self.provider.predict("species", self.images)
            self.assertEqual(caught.exception.code, reason)

    def test_timeout_does_not_expose_key(self):
        self.http.post.side_effect = requests.Timeout("https://example?api-key=private-test-key")
        with self.assertRaises(ProviderError) as caught:
            self.provider.predict("species", self.images)
        self.assertNotIn("private-test-key", str(caught.exception))

    def test_invalid_scores_and_json_rejected(self):
        for value in (float("nan"), float("inf"), -1, 2, "0.98", True):
            self.response.json.return_value = provider_payload(score=value)
            with self.subTest(value=value), self.assertRaises(ProviderError):
                self.provider.predict("species", self.images)
        self.response.json.side_effect = ValueError("bad JSON")
        with self.assertRaises(ProviderError):
            self.provider.predict("species", self.images)


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.provider = FakeProvider()
        self.service = AnalysisService(self.provider)
        self.image = prepare_image(image_bytes(), "leaf")

    def test_requires_consent_before_external_calls(self):
        report = self.service.analyze([self.image], {}, consent=False)
        self.assertEqual(report["status"], "needs_consent")
        self.assertEqual(self.provider.calls, [])

    def test_quality_gate_and_missing_key(self):
        report = self.service.analyze([prepare_image(image_bytes("blank"), "auto")], {}, True)
        self.assertEqual(report["status"], "needs_better_images")
        self.assertEqual(self.provider.calls, [])
        self.provider.configured = False
        self.assertEqual(self.service.analyze([self.image], {}, True)["status"], "needs_configuration")

    def test_duplicate_views_are_not_extra_evidence(self):
        report = self.service.analyze([self.image, self.image], {}, True)
        self.assertEqual(report["images_used"], 1)
        self.assertEqual(report["quality"][1]["status"], "duplicate")
        self.assertEqual(report["species"]["label"], "oak")
        self.assertIsNone(report["accuracy"]["measured"])
        self.assertIsNone(report["age"]["biological_age_years"])
        json.dumps(report, allow_nan=False)

    def test_ambiguous_and_empty_results_abstain(self):
        for candidates in ([{"label": "oak", "score": 0.81}, {"label": "elm", "score": 0.8}], []):
            self.provider.candidates = candidates
            report = self.service.analyze([self.image], {}, True)
            self.assertIsNone(report["species"]["label"])
            self.assertNotEqual(report["health"]["status"], "healthy")

    def test_provider_failure_keeps_other_task_result(self):
        original = self.provider.predict
        def predict(task, images):
            if task == "disease":
                raise ProviderError("quota_exceeded", "Limit tugadi")
            return original(task, images)
        self.provider.predict = predict
        report = self.service.analyze([self.image], {}, True)
        self.assertEqual(report["status"], "partial")
        self.assertEqual(report["species"]["label"], "oak")

    def test_age_uses_record_not_photo(self):
        context = validate_context({"planted_date": "2020-01-01", "dbh_cm": "30"}, date(2025, 1, 1))
        result = age_result(context, date(2025, 1, 1))
        self.assertEqual(result["years_since_planting"], 5.0)
        self.assertIsNone(result["biological_age_years"])
        for data in ({"dbh_cm": "nan"}, {"height_m": "-2"}, {"planted_date": "2099-01-01"}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                validate_context(data)


class APITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.provider = FakeProvider()
        self.store = AnalysisStore(Path(self.temp.name) / "analyses.sqlite3")
        app = Flask(__name__)
        app.config.update(TESTING=True, MAX_CONTENT_LENGTH=52 * 1024 * 1024)
        app.register_blueprint(create_analysis_blueprint(AnalysisService(self.provider), self.store))
        self.client = app.test_client()

    def test_roundtrip_report_persistence(self):
        response = self.client.post('/api/analyze-tree', data={
            "images": [(BytesIO(image_bytes(size=(256, 256))), "../../photo.png")], "organs": "leaf",
            "external_consent": "true", "planted_date": "2020-01-01",
        })
        self.assertEqual(response.status_code, 200)
        report = response.json["report"]
        self.assertEqual(self.client.get('/api/analysis/' + report["id"]).json["report"], report)
        self.assertNotIn("content", json.dumps(report))

    def test_invalid_uploads_and_missing_report(self):
        self.assertEqual(self.client.post('/api/analyze-tree').status_code, 400)
        self.assertEqual(self.client.post('/api/analyze-tree', data={"images": (BytesIO(b'fake'), 'photo.jpg')}).status_code, 400)
        data = {"images": [(BytesIO(b'count-only'), f"{i}.png") for i in range(6)]}
        self.assertEqual(self.client.post('/api/analyze-tree', data=data).status_code, 400)
        self.assertEqual(self.client.get('/api/analysis/00000000-0000-0000-0000-000000000000').status_code, 404)

    def test_total_upload_limit_json_error(self):
        self.client.application.config['MAX_CONTENT_LENGTH'] = 100
        response = self.client.post('/api/analyze-tree', data={"images": (BytesIO(image_bytes(size=(256, 256))), 'photo.png')})
        self.assertEqual(response.status_code, 413)
        self.assertIn('message', response.json)


def test_rows(count=200):
    return [{"sample_id": f"sample-{i}", "tree_id": f"tree-{i}", "split": "test", "task": "species",
             "truth": "oak", "prediction": "oak", "image_sha256": [f"{i:064x}"],
             "provider": "fixture", "model_version": "1", "pipeline_version": "1", "scope": "test-region",
             "label_source": "expert-1"} for i in range(count)]


class EvaluationTests(unittest.TestCase):
    def test_98_percent_point_estimate_does_not_pass_98_percent_gate(self):
        rows = test_rows()
        for row in rows[:4]:
            row['prediction'] = 'elm'
        result = evaluate(rows)['tasks']['species']
        self.assertEqual(result['accuracy'], 0.98)
        self.assertFalse(result['target_supported_on_test_set'])

    def test_large_perfect_set_passes_statistical_gate(self):
        self.assertTrue(evaluate(test_rows(500))['tasks']['species']['target_supported_on_test_set'])

    def test_abstentions_count_as_errors(self):
        rows = test_rows(10)
        rows[0]['prediction'] = None
        result = evaluate(rows)['tasks']['species']
        self.assertEqual(result['accuracy'], 0.9)
        self.assertEqual(result['coverage'], 0.9)
        self.assertEqual(result['accepted_accuracy'], 1.0)

    def test_leakage_repetition_and_version_mixing_rejected(self):
        rows = test_rows(2)
        for mutate in (lambda r: r[1].update(tree_id='tree-0', split='train'),
                       lambda r: r[1].update(image_sha256=r[0]['image_sha256']),
                       lambda r: r[1].update(tree_id='tree-0'),
                       lambda r: r[1].update(model_version='2')):
            changed = deepcopy(rows)
            mutate(changed)
            with self.assertRaises(ValueError):
                evaluate(changed)


if __name__ == '__main__':
    unittest.main()
