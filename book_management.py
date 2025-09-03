from flask import Blueprint, request, jsonify
from datetime import datetime
from db import students, books
from flask_jwt_extended import jwt_required, get_jwt

book_management_bp = Blueprint("book_management_bp", __name__)

#  Issued Books
@book_management_bp.route("/issued_books", methods=["GET"])
@jwt_required()
def get_issued_books():
    jwt_body = get_jwt()
    role = jwt_body.get("role")
    username = jwt_body.get("sub")

    if role not in ["staff", "admin"]:
        return jsonify({"error": "Access denied"}), 403

    issued_books_list = []
    for sid, info in students.items():
        for book in info.get("borrowed_books", []):
            if book["status"] == "Borrowed":
                issued_books_list.append({
                    "book_id": book["book_id"],
                    "book_name": book["book_name"],
                    "borrowed_by_id": sid,
                    "borrowed_by_name": info["student_name"]
                })

    return jsonify({
        "requested_by": username,
        "role": role,
        "issued_books": issued_books_list or []
    }), 200


# Available Books
@book_management_bp.route("/available_books", methods=["GET"])
def get_available_books():
    available_books_list = [
        {"book_id": bid, "book_name": info["book_name"]}
        for bid, info in books.items() if info["available"] == "Yes"
    ]

    if not available_books_list:
        return jsonify({"message": "No books are currently available"}), 200

    return jsonify({"available_books": available_books_list}), 200

# Mark Missing Book 
@book_management_bp.put("/missing_book")
@jwt_required()
def missing_book():
    jwt_body = get_jwt()
    role = jwt_body.get("role")
    username = jwt_body.get("sub")

    if role not in ["staff", "admin"]:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    student_id = data.get("student_id")
    book_id = data.get("book_id")

    if student_id not in students:
        return {"message": "Student not found"}, 404

    borrowed_books = students[student_id]["borrowed_books"]
    for book in borrowed_books:
        if book["book_id"] == book_id and book["status"] == "Borrowed":
            book["fine"] = 500
            book["status"] = "Missing"
            books[book_id]["available"] = "No"
            return jsonify({
                "requested_by": username,
                "role": role,
                "updated_book": book
            }), 200

    return {"message": "Book not found in student's borrowed list"}, 404

# List Missing Books 
@book_management_bp.get("/missed_books")
@jwt_required()
def get_missing_books():
    jwt_body = get_jwt()
    role = jwt_body.get("role")
    username = jwt_body.get("sub")

    if role not in ["staff", "admin"]:
        return jsonify({"error": "Access denied"}), 403

    missing_books = []
    for student_id, student_info in students.items():
        for book in student_info.get("borrowed_books", []):
            if book.get("status") == "Missing":
                missing_books.append({
                    "student_id": student_id,
                    "student_name": student_info["student_name"],
                    "book_id": book["book_id"],
                    "fine": book.get("fine", 0),
                    "due_date": book.get("date_of_returning"),
                })

    return jsonify({
        "requested_by": username,
        "role": role,
        "missing_books": missing_books or []
    }), 200

# Check Overdue Books 
@book_management_bp.put("/check_overdue")
@jwt_required()
def check_overdue():
    jwt_body = get_jwt()
    role = jwt_body.get("role")
    username = jwt_body.get("sub")

    if role not in ["staff", "admin"]:
        return jsonify({"error": "Access denied"}), 403

    today = datetime.now()
    updated_books = []

    for sid, student in students.items():
        for book in student.get("borrowed_books", []):
            if book["status"] == "Borrowed":
                borrow_date = datetime.strptime(book["date_of_issuing"], "%Y-%m-%d")
                days_borrowed = (today - borrow_date).days

                if days_borrowed > 15:
                    book["status"] = "Missing"
                    book["fine"] = 500
                    books[book["book_id"]]["available"] = "No"

                    updated_books.append({
                        "student_id": sid,
                        "student_name": student["student_name"],
                        "book_id": book["book_id"],
                        "book_name": book["book_name"],
                        "status": "Missing",
                        "fine": book["fine"]
                    })

    return jsonify({
        "requested_by": username,
        "role": role,
        "updated_books": updated_books or []
    }), 200

# BOOK MANAGEMENT 
@book_management_bp.route("/books", methods=["GET", "POST", "DELETE"])
@jwt_required()
def manage_books():
    jwt_body = get_jwt()
    role = jwt_body.get("role")
    username = jwt_body.get("sub")

# Adding new book to library
    if request.method == "POST":
        data = request.json
        book_id = data.get("book_id")
        book_name = data.get("book_name")

        if not book_id or not book_name:
            return jsonify({"error": "book_id and book_name are required"}), 400
        if book_id in books:
            return jsonify({"error": "Book ID already exists"}), 400

        books[book_id] = {"book_name": book_name, "available": "Yes"}
        return jsonify({
            "message": f"Book {book_name} added successfully",
            "requested_by": username
        }), 201

# Removing book from Library
    elif request.method == "DELETE":
        data = request.json
        book_id = data.get("book_id")

        if not book_id:
            return jsonify({"error": "book_id is required"}), 400
        if book_id not in books:
            return jsonify({"error": "Book not found"}), 404

        deleted = books.pop(book_id)
        return jsonify({
            "message": f"Book {book_id} deleted successfully",
            "deleted": deleted,
            "requested_by": username
        }), 200
