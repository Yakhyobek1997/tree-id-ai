"""Pl@ntNet species and disease inference. No fabricated fallback predictions."""
import math
from urllib.parse import quote

import requests


class ProviderError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class PlantNetProvider:
    name = "plantnet"

    def __init__(self, api_key="", project="all", timeout=30, http=None):
        self.api_key = api_key.strip()
        self.project = project
        self.timeout = timeout
        self.http = http or requests

    @property
    def configured(self):
        return bool(self.api_key)

    def predict(self, task, images):
        if task not in {"species", "disease"}:
            raise ValueError("Unsupported analysis task")
        if not self.configured:
            raise ProviderError("not_configured", "AI xizmati hali sozlanmagan.")
        route = (f"identify/{quote(self.project, safe='')}" if task == "species"
                 else "diseases/identify")
        try:
            response = self.http.post(
                f"https://my-api.plantnet.org/v2/{route}",
                params={"api-key": self.api_key, "lang": "en", "nb-results": 5},
                data=[("organs", item.organ) for item in images],
                files=[("images", (f"view-{i}.jpg", item.content, "image/jpeg"))
                       for i, item in enumerate(images)],
                timeout=(5, self.timeout), allow_redirects=False,
            )
        except requests.RequestException:
            # Request URLs contain the API key: never expose raw exceptions.
            raise ProviderError("unavailable", "AI xizmatiga ulanib bo'lmadi. Qayta urinib ko'ring.") from None
        if response.status_code in {401, 403}:
            raise ProviderError("unauthorized", "AI xizmati kaliti yoki ruxsatini tekshirish kerak.")
        if response.status_code == 429:
            raise ProviderError("quota_exceeded", "AI xizmati so'rov limiti tugagan.")
        if response.status_code == 404:
            return {"candidates": [], "model_version": None, "rejected": True}
        if response.status_code != 200:
            raise ProviderError("unavailable", "AI xizmati hozir javob bera olmadi.")
        try:
            body = response.json()
            if not isinstance(body, dict) or not isinstance(body.get("results"), list):
                raise ValueError("Invalid response")
            candidates = []
            for row in body["results"]:
                score = row["score"]
                if isinstance(score, bool) or not isinstance(score, (float, int)):
                    raise ValueError("Invalid score")
                if not math.isfinite(score) or not 0 <= score <= 1:
                    raise ValueError("Invalid score")
                if task == "species":
                    taxon = row["species"]
                    label = taxon["scientificNameWithoutAuthor"]
                    candidate = {"label": label, "score": score,
                                 "common_names": taxon.get("commonNames", [])}
                else:
                    label = row["name"]
                    candidate = {"label": label, "score": score,
                                 "description": row.get("description", label)}
                if not isinstance(label, str) or not label.strip():
                    raise ValueError("Invalid label")
                candidates.append(candidate)
            version = body.get("version")
            if version is not None and not isinstance(version, str):
                raise ValueError("Invalid version")
            return {"candidates": sorted(candidates, key=lambda x: x["score"], reverse=True)[:5],
                    "model_version": version, "rejected": False}
        except (ValueError, TypeError, KeyError, AttributeError):
            raise ProviderError("invalid_response", "AI xizmatidan noto'g'ri javob keldi.") from None
