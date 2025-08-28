from flask import Blueprint,request, jsonify
from datetime import datetime, timedelta
from functools import wraps
from db import students, books, librarians, API_KEYS
from utils import require_role


librarians_routes_bp = Blueprint("librarians_routes_bp",__name__)

# Librarian Management
# Adding librarian - admin only
# Add librarian - admin only

@librarians_routes_bp.route("/add_librarian", methods=["POST"])
@require_role("admin")
def add_librarian():
    data = request.json
    librarian_id = data.get("librarian_id")
    name = data.get("name")
    email = data.get("email")
    librarian_name = data.get("librarian_name")

    if not librarian_id or not librarian_name:
        return jsonify({"error": "librarian_id and librarian_name are required"}), 400

    if librarian_id in librarians:
        return jsonify({"error": "Librarian ID already exists"}), 400

    librarians[librarian_id] = {"name": name, "email": email, "role": "staff"}
    return jsonify({"message": f"Librarian {name} added successfully"}), 201
    librarians[librarian_id] = {"librarian_name": librarian_name}
    return jsonify({"message": f"Librarian {librarian_name} added successfully"}), 201

# Removing librarian - admin only
# Remove librarian - admin only
@librarians_routes_bp.route("/remove_librarian/<librarian_id>", methods=["DELETE"])
@require_role("admin")
def remove_librarian(librarian_id):
    if librarian_id not in librarians:
        return jsonify({"error": "Librarian not found"}), 404
    
    removed = librarians.pop(librarian_id)
    return jsonify({"message": f"Librarian {removed['name']} removed"})
    return jsonify({"message": f"Librarian {removed['librarian_name']} removed"})


# List all librarians 
@librarians_routes_bp.route("/list_librarians", methods=["GET"])
def list_librarians():
    result = [{"librarian_id": lid, "librarian_name": info["librarian_name"]} 
              for lid, info in librarians.items()]
    return jsonify({"librarians": result})