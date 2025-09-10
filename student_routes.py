from flask import request, jsonify, Blueprint
from datetime import datetime
from db import students
from flask_jwt_extended import jwt_required, get_jwt
from login_routes import get_current_user

student_routes_bp = Blueprint("student_routes_bp", __name__)

@student_routes_bp.route("/student", methods=["GET", "POST", "PUT"])
@jwt_required(optional=True)   # allow JWT for all, required for GET
def student_actions():
    # Student Entry
    if request.method == "POST":  
        data = request.get_json()
        student_id = data.get("student_id")

        if not student_id:
            return {"message": "student_id is required"}, 400
        if student_id not in students:
            return {"message": "Student not found"}, 404

        students[student_id]["in_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        students[student_id]["out_time"] = None  
        return {
            "student_id": student_id,
            "student_name": students[student_id]["student_name"],
            "in_time": students[student_id]["in_time"]
        }
    
    # Student Exit
    elif request.method == "PUT": 
        data = request.get_json()
        student_id = data.get("student_id")

        if not student_id:
            return {"message": "student_id is required"}, 400
        if student_id not in students:
            return {"message": "Student not found"}, 404
        if not students[student_id].get("in_time"):
            return {"message": "Student has not entered yet"}, 400

        students[student_id]["out_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "student_id": student_id,
            "out_time": students[student_id]["out_time"]
        }
    
    # View Library Entries (staff/admin only)
    elif request.method == "GET":
        jwt_body = get_jwt()
        role = jwt_body.get("role")

        # Only staff and admin allowed
        if role not in ["staff", "admin"]:
            return jsonify({"error": "Only staff and admin can view entered students"}), 403

        entered_students = {
            sid: {
                "student_name": info["student_name"],
                "in_time": info.get("in_time"),
                "out_time": info.get("out_time")
            }
            for sid, info in students.items() if info.get("in_time")
        }

        if not entered_students:
            return jsonify({"message": "No students have entered the library yet"}), 200

        return jsonify({"entered_students": entered_students}), 200
