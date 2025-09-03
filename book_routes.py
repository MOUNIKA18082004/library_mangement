from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from db import students, books, librarians
from flask_jwt_extended import jwt_required, get_jwt

book_routes_bp = Blueprint("book_routes_bp", __name__)

# Borrowing Book 
@book_routes_bp.post("/borrow_book")
@jwt_required()
def borrow_book():
    data = request.get_json()
    student_id = data["student_id"]
    book_id = data["book_id"]
    librarian_id = data["librarian_id"]

    jwt_body = get_jwt()
    role = jwt_body.get("role")
    username = jwt_body.get("sub")

    # Only staff or the student themselves can borrow
    if role not in ["staff", "admin"]:
        return {"error": "Access denied"}, 403

    if student_id not in students:
        return {"message": "Student not found"}, 404
    
    if not students[student_id].get("in_time") or students[student_id].get("out_time"):
        return {"message": "Student must be inside the library to borrow a book"}, 403

    if book_id not in books or books[book_id]["available"] == "No":
        return {"message": "Book not available"}, 400
    if librarian_id not in librarians:
        return {"message": "Librarian not found"}, 404

    active_books = [
        b for b in students[student_id]["borrowed_books"]
        if b["status"] in ["Borrowed", "Missing"]
    ]
    if len(active_books) >= 3:
        return {"message": "Borrowing limit reached (max 3 books allowed)"}, 403

    date_of_issuing = datetime.now()
    date_of_returning = date_of_issuing + timedelta(days=7)

    record = {
        "book_id": book_id,
        "book_name": books[book_id]["book_name"],
        "issued_by": librarian_id,
        "date_of_issuing": date_of_issuing.strftime("%Y-%m-%d"),
        "date_of_returning": date_of_returning.strftime("%Y-%m-%d"),
        "fine": 0,
        "status": "Borrowed"
    }

    students[student_id]["borrowed_books"].append(record)
    books[book_id]["available"] = "No"

    return {
        "student_id": student_id,
        "student_name": students[student_id]["student_name"],
        "borrowed_books_count": len(active_books) + 1,
        "borrowed_book": record
    }


# Book count each member has 
@book_routes_bp.route("/count/<student_id>", methods=["GET"])
@jwt_required()
def get_book_count(student_id):
    jwt_body = get_jwt()
    role = jwt_body.get("role")
    username = jwt_body.get("sub")

    if role not in ["staff", "admin"] and username != student_id:
        return {"error": "Access denied"}, 403

    if student_id not in students:
        return jsonify({"error": "Student ID not found"}), 404

    student = students[student_id]
    book_count = len(student["borrowed_books"])  

    return jsonify({
        "student_id": student_id,
        "student_name": student["student_name"],
        "book_count": book_count,
        "borrowed_books": student["borrowed_books"]
    })


# Returning Book 
@book_routes_bp.put("/return_book")
@jwt_required()
def return_book():
    data = request.get_json()
    student_id = data["student_id"]
    book_id = data["book_id"]

    jwt_body = get_jwt()
    role = jwt_body.get("role")
    username = jwt_body.get("sub")

    if role not in ["staff", "admin"] and username != student_id:
        return {"error": "Access denied"}, 403

    if student_id not in students:
        return {"message": "Student not found"}, 404

    borrowed_books = students[student_id]["borrowed_books"]
    for book in borrowed_books:
        if book["book_id"] == book_id:
            if book["status"] == "Borrowed":
                book["status"] = "Returned"
                book["fine"] = 0
                books[book_id]["available"] = "Yes"
                return {"message": "Book returned successfully"}, 200

            elif book["status"] == "Missing":
                already_paid = 500 - book["fine"]
                book["fine"] = max(250 - already_paid, 0)
                book["status"] = "Returned"
                book["was_missing"] = True
                books[book_id]["available"] = "Yes"
                return {
                    "message": "Missing book returned with reduced fine",
                    "student_id": student_id,
                    "book_id": book_id,
                    "remaining_fine": book["fine"]
                }, 200

            else:
                return {"message": "Book already returned"}, 400

    return {"message": "Book not found in student's borrowed list"}, 404


# Enquiry Books (Public Access) 
@book_routes_bp.get("/book_enquiry/<book_id>")
def book_enquiry(book_id):
    if book_id not in books:
        return {"message": "Book not found"}, 404
    if books[book_id]["available"] == "Yes":
        return {"message": f"Book {book_id} - {books[book_id]['book_name']} is available"}
    else:
        return {"message": f"Book {book_id} - {books[book_id]['book_name']} is NOT available"}


#  Books and Student Details 
@book_routes_bp.route("/students_books", methods=["GET"])
@jwt_required()
def students_books():
    jwt_body = get_jwt()
    role = jwt_body.get("role")
    username = jwt_body.get("sub")

    if role in ["staff", "admin"]:
        all_students_books = {
            sid: {
                "student_name": info["student_name"],
                "borrowed_books": info.get("borrowed_books", [])
            }
            for sid, info in students.items()
        }
        return jsonify({"students_books": all_students_books}), 200

    elif role == "student":
        if username not in students:
            return jsonify({"error": "Student not found"}), 404
        return jsonify({
            "student_id": username,
            "student_name": students[username]["student_name"],
            "borrowed_books": students[username].get("borrowed_books", [])
        }), 200

    return jsonify({"error": "Unauthorized"}), 403
