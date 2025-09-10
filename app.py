from flask import Flask
from flask_jwt_extended import jwt_required, JWTManager, create_access_token, get_jwt
from login_routes import login_bp
from book_routes import book_management_bp
from fine_routes import fine_routes_bp
from librarians_routes import librarians_routes_bp
from membership_routes import membership_routes_bp
from student_routes import student_routes_bp

app = Flask(__name__)
jwt = JWTManager(app)
app.config["JWT_SECRET_KEY"] = "Mounika's_secret_key"


@jwt.unauthorized_loader
def authorizing(err):
    return {"message":"Token is missing"}


app.register_blueprint(login_bp,url_prefix="")
app.register_blueprint(book_management_bp,url_prefix="")
app.register_blueprint(fine_routes_bp,url_prefix="")
app.register_blueprint(librarians_routes_bp,url_prefix="")
app.register_blueprint(membership_routes_bp,url_prefix="")
app.register_blueprint(student_routes_bp,url_prefix="")

# Main function
if __name__ == "__main__":
    app.run(debug=True)