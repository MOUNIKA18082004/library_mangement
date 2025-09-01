from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from db import students, books, librarians
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

#  Display Missed Books 
@book_management_bp.get("/missed_books")
def get_missing_books():
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

    if not missing_books:
        return {"message": "No missing books found"}, 200

    return {"missing_books": missing_books}, 200

# Check Overdue & Mark as Missing 
@book_management_bp.route("/check_overdue", methods=["PUT"])
def check_overdue():
    today = datetime.now()
    updated_books = []

    for sid, student in students.items():
        for book in student.get("borrowed_books", []):
            if book["status"] == "Borrowed":
                borrow_date = datetime.strptime(book["borrow_date"], "%Y-%m-%d")
                days_borrowed = (today - borrow_date).days

                if days_borrowed > 15:
                    # Mark as Missing & Fine = 500
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

    if not updated_books:
        return jsonify({"message": "No overdue books found"}), 200

    return jsonify({
        "message": "Overdue books marked as Missing",
        "updated_books": updated_books
    }), 200

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
