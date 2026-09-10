"""Coordinate quality gates, multi-view inference, uncertainty and measurements."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import math
import uuid

from .provider import ProviderError


PIPELINE_VERSION = "tree-analysis-1.0"


def validate_context(values, today=None):
    today = today or datetime.now(timezone.utc).date()
    context = {}
    for name, maximum in (("dbh_cm", 2000), ("height_m", 150)):
        raw = values.get(name)
        if raw not in (None, ""):
            try:
                number = float(raw)
            except (ValueError, TypeError):
                raise ValueError(f"{name}: musbat son kiriting.") from None
            if not math.isfinite(number) or not 0 < number <= maximum:
                raise ValueError(f"{name}: 0 dan katta, {maximum} dan oshmagan son kiriting.")
            context[name] = number
    planted = values.get("planted_date")
    if planted:
        try:
            parsed = date.fromisoformat(planted)
        except (ValueError, TypeError):
            raise ValueError("Ekilgan sana YYYY-MM-DD formatida bo'lishi kerak.") from None
        if parsed > today:
            raise ValueError("Ekilgan sana kelajakda bo'lishi mumkin emas.")
        context["planted_date"] = parsed.isoformat()
    return context


def age_result(context, today=None):
    today = today or datetime.now(timezone.utc).date()
    planted = context.get("planted_date")
    return {
        "status": "planting_record" if planted else "insufficient_evidence",
        "biological_age_years": None,
        "growth_stage": None,
        "years_since_planting": round((today - date.fromisoformat(planted)).days / 365.2425, 1) if planted else None,
        "message": ("Ekilganidan beri o'tgan vaqt hisoblandi. Ko'chat ekilgandagi yosh bunga kirmaydi."
                    if planted else "Yosh yoki qari ekanini ishonchli baholash uchun tur, ekilgan sana va joyida o'lchovlar kerak."),
        "measurements": {key: context[key] for key in ("dbh_cm", "height_m") if key in context},
        "measurement_source": "user_supplied",
    }


class AnalysisService:
    def __init__(self, provider, minimum_score=0.8, minimum_margin=0.15):
        if not 0 <= minimum_score <= 1 or not 0 <= minimum_margin <= 1:
            raise ValueError("Analysis thresholds must be between 0 and 1")
        self.provider = provider
        self.minimum_score = minimum_score
        self.minimum_margin = minimum_margin

    def capabilities(self):
        return {
            "pipeline_version": PIPELINE_VERSION,
            "provider": self.provider.name, "configured": self.provider.configured,
            "max_images": 5, "requires_external_consent": True,
            "accuracy": {"target": 0.98, "measured": None, "status": "not_evaluated"},
            "disease_scope": "limited_species_and_pathologies",
            "age_method": "planting_record_only",
        }

    def _predict(self, task, images):
        try:
            output = self.provider.predict(task, images)
        except ProviderError as exc:
            return {"status": "unavailable", "reason": exc.code, "message": str(exc),
                    "candidates": [], "label": None, "model_score": None}
        candidates = output["candidates"]
        top = candidates[0] if candidates else None
        margin = top["score"] - candidates[1]["score"] if len(candidates) > 1 else top["score"] if top else 0
        accepted = bool(top and top["score"] >= self.minimum_score and margin >= self.minimum_margin)
        status = "candidate" if accepted else "uncertain" if candidates else "not_identified"
        message = ("Model taklifi; zarur bo'lsa mutaxassis tasdig'ini oling." if accepted
                   else "Ishonchli xulosa uchun qo'shimcha aniq rasmlar kerak.")
        if task == "disease":
            message += " Kasallik modeli qamrovi cheklangan; natija daraxtning sog'lomligini tasdiqlamaydi."
        return {
            "status": status, "label": top["label"] if accepted else None,
            "model_score": top["score"] if top else None, "score_type": "uncalibrated_provider_score",
            "candidates": candidates, "model_version": output.get("model_version"),
            "provider": self.provider.name, "message": message,
            "threshold": self.minimum_score, "margin_required": self.minimum_margin,
        }

    def analyze(self, images, context, consent=False):
        quality = [{"view": i + 1, "organ": img.organ, "sha256": img.sha256, **img.quality}
                   for i, img in enumerate(images)]
        usable = []
        seen = set()
        for i, img in enumerate(images):
            if img.sha256 in seen:
                quality[i] = {**quality[i], "status": "duplicate",
                              "issues": [*quality[i]["issues"], "Takroriy rasm tahlilga qayta qo'shilmadi."]}
            else:
                seen.add(img.sha256)
                if img.quality["status"] != "rejected":
                    usable.append(img)
        report = {
            "id": str(uuid.uuid4()), "created_at": datetime.now(timezone.utc).isoformat(),
            "pipeline_version": PIPELINE_VERSION, "quality": quality,
            "images_used": len(usable), "context": context, "age": age_result(context),
            "accuracy": {"target": 0.98, "measured": None, "status": "not_evaluated"},
            "external_processing": False,
            "recommendations": ["Bitta daraxtning umumiy ko'rinishi, bargi va po'stlog'ini alohida suratga oling."],
        }
        if not usable:
            status, message = "needs_better_images", "Rasm sifatini yaxshilab qayta yuboring."
        elif not self.provider.configured:
            status, message = "needs_configuration", "Tur va kasallik tahlili uchun AI xizmati hali sozlanmagan."
        elif not consent:
            status, message = "needs_consent", "Tur va kasallik tahlili uchun rasmlarni Pl@ntNet xizmatiga yuborishga rozilik kerak."
        else:
            # Independent requests, bounded at two; no retries that consume extra quota.
            with ThreadPoolExecutor(max_workers=2) as pool:
                species_future = pool.submit(self._predict, "species", usable)
                disease_future = pool.submit(self._predict, "disease", usable)
                report["species"] = species_future.result()
                report["health"] = disease_future.result()
            report["external_processing"] = True
            statuses = [report["species"]["status"], report["health"]["status"]]
            report["status"] = "unavailable" if all(s == "unavailable" for s in statuses) else "partial" if "unavailable" in statuses else "completed"
            return report
        report["status"] = status
        for task in ("species", "health"):
            report[task] = {"status": status, "message": message, "candidates": [],
                            "label": None, "model_score": None}
        return report
