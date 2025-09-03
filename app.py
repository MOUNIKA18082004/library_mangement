from flask import Flask
from flask_jwt_extended import jwt_required, JWTManager, create_access_token, get_jwt
from login import login_bp
from book_management import book_management_bp
from book_routes import book_routes_bp
from fine_routes import fine_routes_bp
from librarians_routes import librarians_routes_bp
from membership_routes import membership_routes_bp
from student_routes import student_routes_bp

app = Flask(__name__)
jwt = JWTManager(app)
app.config["JWT_SECRET_KEY"] = "Mounika's_secret_key"

app.register_blueprint(login_bp,url_prefix="")
app.register_blueprint(book_management_bp,url_prefix="/book_manage")
app.register_blueprint(book_routes_bp,url_prefix="/book")
app.register_blueprint(fine_routes_bp,url_prefix="/fine")
app.register_blueprint(librarians_routes_bp,url_prefix="/librarians")
app.register_blueprint(membership_routes_bp,url_prefix="/membership")
app.register_blueprint(student_routes_bp,url_prefix="/student")

# Main function
if __name__ == "__main__":
    app.run(debug=True)