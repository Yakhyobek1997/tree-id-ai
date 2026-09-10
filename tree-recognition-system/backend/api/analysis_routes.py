"""Multi-part multi-view analysis endpoints, independent from image retrieval."""
from flask import Blueprint, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge

from analysis.images import MAX_FILE_BYTES, prepare_image
from analysis.service import validate_context


def create_analysis_blueprint(service, store):
    api = Blueprint("analysis", __name__)

    @api.get("/api/analysis/capabilities")
    def capabilities():
        return jsonify(service.capabilities())

    @api.post("/api/analyze-tree")
    def analyze_tree():
        files = request.files.getlist("images") or request.files.getlist("image")
        organs = request.form.getlist("organs") or ["auto"] * len(files)
        if not 1 <= len(files) <= 5:
            return jsonify(message="Bitta daraxtning 1 tadan 5 tagacha rasmini yuboring."), 400
        if len(organs) != len(files):
            return jsonify(message="Har bir rasm uchun bitta qism tanlang."), 400
        try:
            context = validate_context(request.form)
            images = [prepare_image(file.read(MAX_FILE_BYTES + 1), organ)
                      for file, organ in zip(files, organs)]
        except ValueError as exc:
            return jsonify(message=str(exc)), 400
        report = service.analyze(images, context, consent=request.form.get("external_consent") == "true")
        store.save(report)
        return jsonify(success=True, report=report), 200

    @api.get("/api/analysis/<uuid:report_id>")
    def get_analysis(report_id):
        report = store.get(str(report_id))
        if report is None:
            return jsonify(message="Tahlil topilmadi."), 404
        return jsonify(report=report)

    @api.app_errorhandler(RequestEntityTooLarge)
    def too_large(_error):
        return jsonify(message="So'rov hajmi ruxsat etilgan limitdan oshdi. Rasmlarni kichraytiring."), 413

    return api
