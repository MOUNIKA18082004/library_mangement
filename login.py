from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt
from db import students, users

login_bp = Blueprint("login_bp",__name__)

@login_bp.post("/login")
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # Case 1: Admin/Staff login
    if username in users:
        if users[username]["password"] == password:
            role = users[username]["role"]
            token = create_access_token(identity=username, additional_claims={"role": role})
            return jsonify({"access_token": token, "role": role}), 200
        return jsonify({"msg": "Invalid password"}), 401

    # Case 2: Student login (use student_id + password)
    if username in students:
        if students[username]["password"] == password:
            role = "student"
            token = create_access_token(identity=username, additional_claims={"role": role})
            return jsonify({"access_token": token, "role": role}), 200
        return jsonify({"msg": "Invalid student password"}), 401

    return jsonify({"msg": "User not found"}), 404
 
def get_current_user(): # Extract role and username from JWT
    jwt_body = get_jwt()
    return jwt_body.get("role"), jwt_body.get("sub")
