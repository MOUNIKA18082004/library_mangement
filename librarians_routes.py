from flask import Blueprint, request, jsonify
from db import librarians, API_KEYS

librarians_routes_bp = Blueprint("librarians_routes_bp", __name__)

# ---------- Unified Librarian Management ----------
@librarians_routes_bp.route("/librarians", methods=["GET", "POST", "DELETE"])
def manage_librarians():
    if request.method == "GET":  # List all librarians
        result = [
            {
                "librarian_id": lid,
                "librarian_name": info.get("librarian_name"),
                "name": info.get("name"),
                "email": info.get("email"),
                "role": info.get("role")
            }
            for lid, info in librarians.items()
        ]
        return jsonify({"librarians": result}), 200

    elif request.method == "POST":  # Add librarian (admin check via header)
        data = request.json
        librarian_id = data.get("librarian_id")
        librarian_name = data.get("librarian_name")
        name = data.get("name")
        email = data.get("email")

        is_admin = request.headers.get("X-API-KEY") == API_KEYS.get("admin_key")
        if not is_admin:
            return jsonify({"error": "Admin privilege required"}), 403

        if not librarian_id or not librarian_name:
            return jsonify({"error": "librarian_id and librarian_name are required"}), 400

        if librarian_id in librarians:
            return jsonify({"error": "Librarian ID already exists"}), 400

        librarians[librarian_id] = {
            "librarian_name": librarian_name,
            "name": name,
            "email": email,
            "role": "staff"
        }
        return jsonify({"message": f"Librarian {librarian_name} added successfully"}), 201

    elif request.method == "DELETE":  # Remove librarian (admin only)
        data = request.json
        librarian_id = data.get("librarian_id")

        is_admin = request.headers.get("X-API-KEY") == API_KEYS.get("admin_key")
        if not is_admin:
            return jsonify({"error": "Admin privilege required"}), 403

        if not librarian_id:
            return jsonify({"error": "librarian_id is required"}), 400

        if librarian_id not in librarians:
            return jsonify({"error": "Librarian not found"}), 404

        removed = librarians.pop(librarian_id)
        return jsonify({"message": f"Librarian {removed['librarian_name']} removed"}), 200
