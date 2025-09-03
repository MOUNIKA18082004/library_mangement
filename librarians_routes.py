from flask import Blueprint, request, jsonify
from db import librarians
from flask_jwt_extended import jwt_required, get_jwt

librarians_routes_bp = Blueprint("librarians_routes_bp", __name__)

@librarians_routes_bp.route("/librarians", methods=["GET", "POST", "DELETE"])
@jwt_required()
def manage_librarians():
    jwt_body = get_jwt()
    role = jwt_body.get("role")  # custom claim from JWT (set at login)

    # List all librarians 
    if request.method == "GET":
        result = [
            {
                "librarian_id": lid,
                "librarian_name": info.get("librarian_name"),
            }
            for lid, info in librarians.items()
        ]
        return jsonify({"librarians": result}), 200

    #  Add librarian (Admin only) 
    elif request.method == "POST":
        if role != "admin":
            return jsonify({"error": "Only admin can add librarians"}), 403

        data = request.json
        librarian_id = data.get("librarian_id")
        librarian_name = data.get("librarian_name")


        if not librarian_id or not librarian_name:
            return jsonify({"error": "librarian_id and librarian_name are required"}), 400

        if librarian_id in librarians:
            return jsonify({"error": "Librarian ID already exists"}), 400

        librarians[librarian_id] = {
            "librarian_name": librarian_name,
            "role": "staff"  # default role
        }
        return jsonify({
            "message": f"Librarian {librarian_name} added successfully",
            "librarian": librarians[librarian_id]
        }), 201

    # Remove librarian (Admin only) 
    elif request.method == "DELETE":
        if role != "admin":
            return jsonify({"error": "Only admin can remove librarians"}), 403

        data = request.json
        librarian_id = data.get("librarian_id")

        if not librarian_id:
            return jsonify({"error": "librarian_id is required"}), 400

        if librarian_id not in librarians:
            return jsonify({"error": "Librarian not found"}), 404

        removed = librarians.pop(librarian_id)
        return jsonify({
            "message": f"Librarian {removed['librarian_name']} removed successfully"
        }), 200
