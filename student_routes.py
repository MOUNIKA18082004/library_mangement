from flask import request, jsonify, Blueprint
from datetime import datetime
from db import students

student_routes_bp = Blueprint("student_routes_bp",__name__)

# Student Entry
@student_routes_bp.post("/student_entry")
def student_entry():
    data = request.get_json()
    student_id = data["student_id"]

    if not student_id:
        return {"message": "student_id is required"}, 400

    if student_id not in students:
        return {"message": "Student not found"}, 404

    # Record entry time
    students[student_id]["in_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    students[student_id]["out_time"] = None  
    return {
        "student_id": student_id,
        "student_name": students[student_id]["student_name"],
        "in_time": students[student_id]["in_time"]
    }

# Student Exit
@student_routes_bp.put("/student_exit")
def student_exit():
    data = request.get_json()
    student_id = data.get("student_id")

    if not student_id:
        return {"message": "student_id is required"}, 400

    if student_id not in students:
        return {"message": "Student not found"}, 404

    # Check if student has entered
    if not students[student_id].get("in_time"):
        return {"message": "Student has not entered yet"}, 400

    # Record exit time
    students[student_id]["out_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "student_id": student_id,
        "out_time": students[student_id]["out_time"]
    }

# Students who have entered and left
@student_routes_bp.route("/library_entries", methods=["GET"])
def view_library_entries():
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