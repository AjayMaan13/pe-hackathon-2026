from flask import Blueprint, jsonify, redirect, request
from peewee import IntegrityError
from playhouse.shortcuts import model_to_dict

from app.models.url import URL, generate_short_code

urls_bp = Blueprint("urls", __name__)


@urls_bp.route("/shorten", methods=["POST"])
def shorten_url():
    data = request.get_json()

    if not data or "url" not in data:
        return jsonify({"error": "Missing 'url' field in request body"}), 400

    original_url = data["url"].strip()

    if not original_url:
        return jsonify({"error": "URL cannot be empty"}), 400

    if not original_url.startswith(("http://", "https://")):
        return jsonify({"error": "URL must start with http:// or https://"}), 400

    for _ in range(5):
        short_code = generate_short_code()
        try:
            url_record = URL.create(
                original_url=original_url,
                short_code=short_code
            )
            return jsonify({
                "short_code": url_record.short_code,
                "short_url": f"{request.host_url}{url_record.short_code}",
                "original_url": url_record.original_url
            }), 201
        except IntegrityError:
            continue

    return jsonify({"error": "Could not generate unique code, try again"}), 500


@urls_bp.route("/<string:code>", methods=["GET"])
def redirect_to_url(code):
    try:
        url_record = URL.get(URL.short_code == code)
        return redirect(url_record.original_url, code=302)
    except URL.DoesNotExist:
        return jsonify({"error": f"Short code '{code}' not found"}), 404


@urls_bp.route("/urls", methods=["GET"])
def list_urls():
    urls = URL.select().order_by(URL.created_at.desc())
    return jsonify([model_to_dict(u) for u in urls]), 200