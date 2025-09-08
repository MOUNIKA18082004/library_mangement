from flask import Blueprint, request, jsonify
from datetime import datetime,timedelta
from db import students, books,librarians
from flask_jwt_extended import jwt_required
from login_routes import get_current_user   

book_management_bp = Blueprint("book_management_bp", __name__)

#  Borrowing Book   
@book_management_bp.post("/borrow_book")
@jwt_required()
def borrow_book():
    role, username = get_current_user()

    data = request.get_json()
    student_id = data["student_id"]
    book_id = data["book_id"]
    librarian_id = data["librarian_id"]

    # Only staff or admin can borrow for students
    if role not in ["staff", "admin"]:
        return {"error": "Access denied"}, 403      #  Forbidden Error

    if student_id not in students:
        return {"message": "Student not found"}, 404
    
    if not students[student_id].get("in_time") or students[student_id].get("out_time"):
        return {"message": "Student must be inside the library to borrow a book"}, 403

    if book_id not in books or books[book_id]["available"] == "No":
        return {"message": "Book not available"}, 400       #  Bad Request
    if librarian_id not in librarians:
        return {"message": "Librarian not found"}, 404

    # Check borrowing limit
    active_books = [
        b for b in students[student_id]["borrowed_books"]
        if b["status"] in ["Borrowed", "Missing"]
    ]
    if len(active_books) >= 3:
        return {"message": "Borrowing limit reached (max 3 books allowed)"}, 403

    # Create borrowing record
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

#  Book Count Each Member 
@book_management_bp.route("/count/<student_id>", methods=["GET"])
@jwt_required()
def get_book_count(student_id):
    role, username = get_current_user()

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
@book_management_bp.put("/return_book")
@jwt_required()
def return_book():
    role, username = get_current_user()

    data = request.get_json()
    student_id = data["student_id"]
    book_id = data["book_id"]

    if role not in ["staff", "admin"] and username != student_id:
        return {"error": "Access denied"}, 403

    if student_id not in students:
        return {"message": "Student not found"}, 404

    borrowed_books = students[student_id]["borrowed_books"]
    for book in borrowed_books:
        if book["book_id"] == book_id:
            # Normal return
            if book["status"] == "Borrowed":
                book["status"] = "Returned"
                book["fine"] = 0
                books[book_id]["available"] = "Yes"
                return {"message": "Book returned successfully"}, 200

            # Returning a missing book
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

# Enquiry Books (Public) -
@book_management_bp.get("/book_enquiry/<book_id>")
def book_enquiry(book_id):
    if book_id not in books:
        return {"message": "Book not found"}, 404
    if books[book_id]["available"] == "Yes":
        return {"message": f"Book {book_id} - {books[book_id]['book_name']} is available"}
    else:
        return {"message": f"Book {book_id} - {books[book_id]['book_name']} is NOT available"}

# Books and Student Details 
@book_management_bp.route("/students_books", methods=["GET"])
@jwt_required()
def students_books():
    role, username = get_current_user()

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

# Issued Books 
@book_management_bp.route("/issued_books", methods=["GET"])
@jwt_required()
def get_issued_books():
    role, username = get_current_user()   
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

#  Mark Missing Book 
@book_management_bp.put("/missing_book")
@jwt_required()
def missing_book():
    role, username = get_current_user()

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
    role, username = get_current_user()

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
    role, username = get_current_user()

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

#  Book Management 
@book_management_bp.route("/books", methods=["GET", "POST", "DELETE"])
@jwt_required()
def manage_books():
    role, username = get_current_user()

    # GET all books 
    if request.method == "GET":
        result = [
            {"book_id": bid, "book_name": info["book_name"], "available": info["available"]}
            for bid, info in books.items()
        ]
        return jsonify({
            "requested_by": username,
            "role": role,
            "total_books": len(result),
            "books": result
        }), 200

    # Only admin can add/delete books
    if role != "admin":
        return jsonify({"error": "Admin privilege required"}), 403

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
