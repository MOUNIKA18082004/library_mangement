from flask import Blueprint, request, jsonify
from db import students
from flask_jwt_extended import jwt_required
from login_routes import get_current_user   

fine_routes_bp = Blueprint("fine_routes_bp", __name__)

# Checking Fines 
@fine_routes_bp.get("/fines/<student_id>")
@jwt_required()
def get_student_fines(student_id):
    role, username = get_current_user()

    # Only admin/staff OR the student themselves can view
    if role not in ["admin", "staff"] and username != student_id:
        return {"error": "Access denied. You can only view your own fines."}, 403

    if student_id not in students:
        return {"error": "Student not found"}, 404

    student = students[student_id]
    fines_list = []

    for book in student["borrowed_books"]:
        if book.get("fine", 0) > 0 and book.get("status") in ["Returned", "Missing"]:
            fines_list.append({
                "student_id": student_id,
                "student_name": student["student_name"],
                "book_id": book["book_id"],
                "book_name": book["book_name"],
                "status": book["status"],
                "fine": book["fine"],
                "was_missing": book.get("was_missing", False)
            })

    if not fines_list:
        return {"message": f"No fines pending for student {student_id}"}, 200

    return {"fines": fines_list}, 200

# View All Students with Fines 
@fine_routes_bp.route("/students_fines", methods=["GET"])
@jwt_required()
def students_fines():
    role, username = get_current_user()

    if role not in ["admin", "staff"]:
        return jsonify({"error": "Only librarians (staff/admin) can view fines"}), 403

    students_with_fines = {}
    for sid, info in students.items():
        fines = []
        for book in info.get("borrowed_books", []):
            if book.get("fine", 0) > 0 and book.get("status") in ["Returned", "Missing"]:
                fines.append({
                    "book_id": book["book_id"],
                    "book_name": book["book_name"],
                    "fine": book["fine"],
                    "status": book["status"],
                    "was_missing": book.get("was_missing", False)
                })
        if fines:
            students_with_fines[sid] = {
                "student_name": info["student_name"],
                "fines": fines
            }

    if not students_with_fines:
        return jsonify({"message": "No fines pending"}), 200

    return jsonify({"students_with_fines": students_with_fines}), 200

# Paying Fine 
@fine_routes_bp.put("/pay_fine/<student_id>")
@jwt_required()
def pay_fine(student_id):
    role, username = get_current_user()

    if role not in ["admin", "staff"]:
        return jsonify({"error": "Only librarians (staff/admin) can process fines"}), 403

    if student_id not in students:
        return jsonify({"error": "Student not found"}), 404

    student = students[student_id]
    total_fine = sum(book.get("fine", 0) for book in student["borrowed_books"])

    if total_fine == 0:
        return jsonify({"message": "No fine pending"}), 200

    data = request.json
    amount = data.get("amount")

    if not amount or amount <= 0:
        return jsonify({"error": "Please provide a valid payment amount"}), 400

    if amount > total_fine:
        return jsonify({"error": f"Payment exceeds pending fine. Pending fine is {total_fine}"}), 400

    # Deduct amount from fines
    remaining = amount
    for book in student["borrowed_books"]:
        if book.get("fine", 0) > 0 and remaining > 0:
            if remaining >= book["fine"]:
                remaining -= book["fine"]
                book["fine"] = 0
            else:
                book["fine"] -= remaining
                remaining = 0

    new_total_fine = sum(book.get("fine", 0) for book in student["borrowed_books"])

    return jsonify({
        "message": f"Payment successful. Paid {amount}.",
        "student_id": student_id,
        "student_name": student["student_name"],
        "paid_amount": amount,
        "remaining_fine": new_total_fine
    }), 200
