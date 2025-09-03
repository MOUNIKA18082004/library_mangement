from flask import request, jsonify, Blueprint
from db import students
from flask_jwt_extended import jwt_required, get_jwt

membership_routes_bp = Blueprint("membership_routes_bp", __name__)


@membership_routes_bp.route("/members", methods=["GET", "POST", "DELETE"])
@jwt_required()
def members():
    jwt_body = get_jwt()
    current_user = jwt_body.get("sub")   # usually username or student_id
    role = jwt_body.get("role")          # custom role claim if you add it when logging in

    # List Members 
    if request.method == "GET":
        members_list = [
            {"student_id": sid, "student_name": info["student_name"]}
            for sid, info in students.items()
        ]
        return jsonify({
            "total_members": len(members_list),
            "members": members_list
        }), 200

    #  Register Student (Admin only) 
    elif request.method == "POST":
        if role != "admin":   # only admin can register
            return jsonify({"msg": "Only admin can register students"}), 403

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

    # DELETE: Remove Student 
    elif request.method == "DELETE":
        data = request.json
        student_id = data.get("student_id")
        password = data.get("password")

        if not student_id:
            return jsonify({"error": "student_id is required"}), 400
        if student_id not in students:
            return jsonify({"error": "Student not found"}), 404

        student = students[student_id]
        total_fine = sum(book.get("fine", 0) for book in student["borrowed_books"])

        # Admin removing student 
        if role == "admin":
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

        # Student self-removal 
        if current_user != student_id:
            return jsonify({"error": "You can only remove your own account"}), 403

        if not password or password != student.get("password"):
            return jsonify({"error": "Password incorrect"}), 403

        if total_fine > 0:   #  student can only remove if fine == 0
            return jsonify({
                "message": f"Cannot remove student {student_id}. Pending fine: {total_fine}. Please contact admin.",
                "fine": total_fine
            }), 400

        students.pop(student_id)
        return jsonify({
            "message": f"Student {student_id} membership declined successfully (no pending fine)",
            "fine": 0
        })
