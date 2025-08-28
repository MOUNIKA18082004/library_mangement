from flask import Blueprint,request, jsonify
from datetime import datetime, timedelta
from functools import wraps
from db import students, books, librarians, API_KEYS
from utils import require_role

book_routes_bp = Blueprint("book_routes_bp",__name__)
# Borrowing book
@book_routes_bp.post("/borrow_book")
def borrow_book():
    data = request.get_json()
    student_id = data["student_id"]
    book_id = data["book_id"]
    librarian_id = data["librarian_id"]

    if student_id not in students:
        return {"message": "Student not found"}, 404
    if book_id not in books or books[book_id]["available"] == "No":
        return {"message": "Book not available"}, 400
    if librarian_id not in librarians:
        return {"message": "Librarian not found"}, 404

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
        "borrowed_books_count": len(students[student_id]["borrowed_books"]),
        "borrowed_book": record
    }

# Book count each member has
@book_routes_bp.route("/count/<student_id>", methods=["GET"])
def get_book_count(student_id):
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
def return_book():
    data = request.get_json()
    student_id = data["student_id"]
    book_id = data["book_id"]

    if student_id not in students:
        return {"message": "Student not found"}, 404

    borrowed_books = students[student_id]["borrowed_books"]
    for book in borrowed_books:
        if book["book_id"] == book_id and book["status"] == "Borrowed":
            today = datetime.now()
            due_date = datetime.strptime(book["date_of_returning"], "%Y-%m-%d")
            actual_return_date = today.strftime("%Y-%m-%d")

            # Fine if late
            if today > due_date:
                delay = (today - due_date).days
                book["fine"] = delay * 2
            else:
                book["fine"] = 0

            book["status"] = "Returned"
            book["date_of_returning"] = actual_return_date
            books[book_id]["available"] = "Yes"

            # Remove returned book from student's borrowed list
            borrowed_books.remove(book)

            return {
                "message": "Book returned successfully",
                "book_id": book_id,
                "fine": book["fine"]
            }

    return {"message": "Book not found in student's borrowed list"}, 404

# Enquiry Books
@book_routes_bp.get("/book_enquiry/<book_id>")
def book_enquiry(book_id):
    if book_id not in books:
        return {"message": "Book not found"}, 404
    if books[book_id]["available"] == "Yes":
        return {"message": f"Book {book_id} - {books[book_id]['book_name']} is available"}
    else:
        return {"message": f"Book {book_id} - {books[book_id]['book_name']} is NOT available"}

# Books and Student Details
@book_routes_bp.route("/students_books", methods=["GET"])
def students_books():
    all_students_books = {}
    for sid, info in students.items():
        all_students_books[sid] = {
            "student_name": info["student_name"],
            "borrowed_books": info.get("borrowed_books", [])
        }
    if not all_students_books:
        return jsonify({"message": "No students found"}), 200
    return jsonify({"students_books": all_students_books}), 200
