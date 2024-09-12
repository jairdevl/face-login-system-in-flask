import os
import re
import io
import zlib
import secrets
import mysql.connector
from werkzeug.utils import secure_filename
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for, Response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import face_recognition
from PIL import Image
from base64 import b64encode, b64decode

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Settings database
app.config["MARIADB_HOST"] = "localhost"
app.config["MARIADB_USER"] = "root"
app.config["MARIADB_PASSWORD"] = "whoami"
app.config["MARIADB"] = "mariadb"
app.config["SECRET_KEY"] = secrets.token_hex(16)

# Connection database
def get_db_connection():
    return mysql.connector.connect(
        host=app.config["MARIADB_HOST"],
        user=app.config["MARIADB_USER"],
        password=app.config["MARIADB_PASSWORD"],
        database=app.config["MARIADB"],
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )

# Create table database
with get_db_connection() as cnx:
    cursor = cnx.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL UNIQUE,
        hash VARCHAR(255) NOT NULL
    )
    """
    cursor.execute(query)
    cnx.commit()

@app.route("/")
@login_required
def home():
    return redirect("/home")

@app.route("/home")
@login_required
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        input_username = request.form.get("username")
        input_password = request.form.get("password")

        if not input_username:
            return render_template("login.html", messager=1)
        elif not input_password:
            return render_template("login.html", messager=2)

        with get_db_connection() as cnx:
            cursor = cnx.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (input_username,))
            user = cursor.fetchone()

        if user is None or not check_password_hash(user["hash"], input_password):
            return render_template("login.html", messager=3)

        session["user_id"] = user["id"]
        return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        input_username = request.form.get("username")
        input_password = request.form.get("password")
        input_confirmation = request.form.get("confirmation")

        if not input_username:
            return render_template("register.html", messager=1)
        elif not input_password:
            return render_template("register.html", messager=2)
        elif not input_confirmation:
            return render_template("register.html", messager=4)
        elif input_password != input_confirmation:
            return render_template("register.html", messager=3)

        with get_db_connection() as cnx:
            cursor = cnx.cursor()
            cursor.execute("SELECT username FROM users WHERE username = %s", (input_username,))
            if cursor.fetchone():
                return render_template("register.html", messager=5)

            hashed_password = generate_password_hash(input_password, method="pbkdf2:sha256", salt_length=8)
            cursor.execute("INSERT INTO users (username, hash) VALUES (%s, %s)", (input_username, hashed_password))
            cnx.commit()
            new_user_id = cursor.lastrowid

        session["user_id"] = new_user_id
        flash(f"Registered as {input_username}")
        return redirect("/")

    return render_template("register.html")

@app.route("/facereg", methods=["GET", "POST"])
def facereg():
    session.clear()
    if request.method == "POST":
        encoded_image = (request.form.get("pic") + "==").encode('utf-8')
        username = request.form.get("name")

        with get_db_connection() as cnx:
            cursor = cnx.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

        if not user:
            return render_template("camera.html", message=1)

        id_ = user['id']
        compressed_data = zlib.compress(encoded_image, 9)
        uncompressed_data = zlib.decompress(compressed_data)
        decoded_data = b64decode(uncompressed_data)

        dir_path = './static/face/unknown/'
        file_path = os.path.join(dir_path, f'{id_}.jpg')

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        try:
            with open(file_path, 'wb') as new_image_handle:
                new_image_handle.write(decoded_data)
        except IOError:
            return render_template("camera.html", message="Error saving image")

        try:
            image_of_bill = face_recognition.load_image_file(f'./static/face/{id_}.jpg')
            bill_face_encoding = face_recognition.face_encodings(image_of_bill)[0]
        except (FileNotFoundError, IndexError):
            return render_template("camera.html", message=5)

        try:
            unknown_image = face_recognition.load_image_file(file_path)
            unknown_face_encoding = face_recognition.face_encodings(unknown_image)[0]
        except (FileNotFoundError, IndexError):
            return render_template("camera.html", message=2)

        results = face_recognition.compare_faces([bill_face_encoding], unknown_face_encoding)

        if results[0]:
            session["user_id"] = user["id"]
            return redirect("/")
        else:
            return render_template("camera.html", message=3)

    return render_template("camera.html")

@app.route("/facesetup", methods=["GET", "POST"])
def facesetup():
    if request.method == "POST":
        encoded_image = (request.form.get("pic") + "==").encode('utf-8')

        with get_db_connection() as cnx:
            cursor = cnx.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE id = %s", (session["user_id"],))
            user = cursor.fetchone()

        if not user:
            return render_template("face.html", message=1)

        id_ = user["id"]
        compressed_data = zlib.compress(encoded_image, 9)
        uncompressed_data = zlib.decompress(compressed_data)
        decoded_data = b64decode(uncompressed_data)

        with open(f'./static/face/{id_}.jpg', 'wb') as new_image_handle:
            new_image_handle.write(decoded_data)

        try:
            image_of_bill = face_recognition.load_image_file(f'./static/face/{id_}.jpg')
            face_recognition.face_encodings(image_of_bill)[0]
        except IndexError:
            return render_template("face.html", message=1)

        return redirect("/home")

    return render_template("face.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("error.html", e=e)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    app.run()