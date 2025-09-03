from flask import request, jsonify, Blueprint
from db import students, books, librarians, API_KEYS

membership_routes_bp = Blueprint("membership_routes_bp", __name__)

# ---------- Single Route ----------
@membership_routes_bp.route("/members", methods=["GET", "POST", "DELETE"])
def members():
    if request.method == "GET":  # List Members
        members_list = [
            {"student_id": sid, "student_name": info["student_name"]}
            for sid, info in students.items()
        ]
        return jsonify({
            "total_members": len(members_list),
            "members": members_list
        }), 200

    elif request.method == "POST":  # Register Student (Admin-like)
        data = request.json
        student_id = data.get("student_id")
        student_name = data.get("student_name")
        password = data.get("password")

        if not student_id or not student_name or not password:
            return jsonify({"error": "student_id, student_name, and password are required"}), 400

        if student_id in students:
            return jsonify({"error": "Student ID already exists"}), 400

        students[student_id] = {
            "student_name": student_name,
            "borrowed_books": [],
            "fine": 0,
            "password": password
        }

        return jsonify({
            "message": f"Student {student_name} registered successfully",
            "student": {
                "student_id": student_id,
                "student_name": student_name,
                "borrowed_books": [],
                "fine": 0,
                "password": "######"  # masked
            }
        }), 201

    elif request.method == "DELETE":  # Remove Student
        data = request.json
        student_id = data.get("student_id")
        password = data.get("password")  # provided by student
        is_admin = request.headers.get("X-API-KEY") == API_KEYS.get("admin_key")

        if not student_id:
            return jsonify({"error": "student_id is required"}), 400

        if student_id not in students:
            return jsonify({"error": "Student not found"}), 404

        student = students[student_id]
        # Calculate fines from borrowed books
        total_fine = sum(book.get("fine", 0) for book in student["borrowed_books"])

        if is_admin:
            if total_fine > 0:
                return jsonify({
                    "message": f"Admin cannot remove student {student_id} because pending fine is {total_fine}",
                    "fine": total_fine
                }), 400
            students.pop(student_id)
            return jsonify({
                "message": f"Student {student_id} membership declined by admin (no pending fine)",
                "fine": 0
            })

        # Student self-request
        if not password or password != student.get("password"):
            return jsonify({"error": "Password incorrect"}), 403

        if total_fine == 0:
            students.pop(student_id)
            return jsonify({
                "message": f"Student {student_id} membership declined successfully (no pending fine)",
                "fine": 0
            })
        else:
            return jsonify({
                "message": f"Cannot remove student {student_id}. Pending fine: {total_fine}. Please contact admin.",
                "fine": total_fine
            }), 400
