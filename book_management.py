from flask import Blueprint,request, jsonify
from datetime import datetime, timedelta
from functools import wraps
from db import students, books, librarians, API_KEYS
from utils import require_role

book_management_bp = Blueprint("book_management_bp",__name__)

# Books currently issued (borrowed)
@book_management_bp.route("/issued_books", methods=["GET"])
def get_issued_books():
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

    if not issued_books_list:
        return jsonify({"message": "No books are currently issued"}), 200

    return jsonify({"issued_books": issued_books_list}), 200

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

# If Book is Missing
@book_management_bp.put("/missing_book")
def missing_book():
    data = request.get_json()
    student_id = data["student_id"]
    book_id = data["book_id"]

    if student_id not in students:
        return {"message": "Student not found"}, 404

    borrowed_books = students[student_id]["borrowed_books"]
    for book in borrowed_books:
        if book["book_id"] == book_id and book["status"] == "Borrowed":
            book["fine"] = 500
            book["status"] = "Missing"
            books[book_id]["available"] = "No"
            return book

    return {"message": "Book not found in student's borrowed list"}, 404

# Book Management
# Adding book - admin only
@book_management_bp.route("/add_book", methods=["POST"])
@require_role("admin")
def add_book_admin():
    data = request.json
    book_id = data.get("book_id")
    book_name = data.get("book_name")

    if book_id in books:
        return jsonify({"error": "Book ID already exists"}), 400

    books[book_id] = {"book_name": book_name, "available": "Yes"}
    return jsonify({"message": f"Book {book_name} added successfully"}), 201

# Removing book - admin only
@book_management_bp.route("/delete_book/<book_id>", methods=["DELETE"])
@require_role("admin")
def delete_book_admin(book_id):
    if book_id not in books:
        return jsonify({"error": "Book not found"}), 404

    deleted = books.pop(book_id)
    return jsonify({"message": f"Book {book_id} deleted successfully", "deleted": deleted})
