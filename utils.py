from functools import wraps
from flask import request, jsonify
from db import students, books, librarians, API_KEYS

def require_role(role="admin"):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            api_key = request.headers.get("X-API-KEY")
            if not api_key or api_key not in API_KEYS.values():
                return jsonify({"error": "Unauthorized - API Key required"}), 401

            if role == "admin" and api_key != API_KEYS["admin_key"]:
                return jsonify({"error": "Forbidden - Admin access only"}), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator
