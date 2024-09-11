# Import libreries
import os
import secrets
import zlib
import mysql.connector
import face_recognition
from base64 import b64decode
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.exceptions import HTTPException, InternalServerError, default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps


# Settings application
app = Flask(__name__)

app.config.update(
    MARIADB_HOST="localhost",
    MARIADB_USER="root",
    MARIADB_PASSWORD="whoami",
    MARIADB="mariadb",
    SECRET_KEY=secrets.token_hex(16),
    SESSION_FILE_DIR=os.path.join(os.getcwd(), 'flask_session'),
    SESSION_PERMANENT=False,
    SESSION_TYPE="filesystem"
)

# Connection database
cnx = mysql.connector.connect(
    host=app.config["MARIADB_HOST"],
    user=app.config["MARIADB_USER"],
    password=app.config["MARIADB_PASSWORD"],
    database=app.config["MARIADB"],
    charset='utf8mb4',
    collation='utf8mb4_unicode_ci'
)

cursor = cnx.cursor()

# Create table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hash VARCHAR(255) NOT NULL
)
""")
cnx.commit()

# Configure sessions flask
Session(app)

# Fuctions
def escape(s):
    replacements = {
        "-": "--", " ": "-", "_": "__", "?": "~q",
        "%": "~p", "#": "~h", "/": "~s", "\"": "''"
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    return s

def apology(message, code=400):
    """Renderizar un mensaje como una disculpa al usuario."""
    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """Decora rutas para requerir inicio de sesión."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Define routes
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
    """Iniciar sesión del usuario"""
    session.clear()
    if request.method == "POST":
        input_username = request.form.get("username")
        input_password = request.form.get("password")
        if not input_username or not input_password:
            return render_template("login.html", messager=1 if not input_username else 2)

        cursor.execute("SELECT * FROM users WHERE username = %s", (input_username,))
        user = cursor.fetchone()

        if user is None or not check_password_hash(user[2], input_password):
            return render_template("login.html", messager=3)

        session["user_id"] = user[0]
        return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():
    """Cerrar sesión del usuario"""
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Registrar nuevo usuario"""
    if request.method == "POST":
        input_username = request.form.get("username")
        input_password = request.form.get("password")
        input_confirmation = request.form.get("confirmation")

        if not input_username or not input_password or not input_confirmation:
            return render_template("register.html", messager=1 if not input_username else 2 if not input_password else 4)

        if input_password != input_confirmation:
            return render_template("register.html", messager=3)

        cursor.execute("SELECT username FROM users WHERE username = %s", (input_username,))
        if cursor.fetchone() is not None:
            return render_template("register.html", messager=5)

        cursor.execute("INSERT INTO users (username, hash) VALUES (%s, %s)",
                       (input_username, generate_password_hash(input_password, method="pbkdf2:sha256", salt_length=8)))
        cnx.commit()
        session["user_id"] = cursor.lastrowid
        flash(f"Registrado como {input_username}")
        return redirect("/")

    return render_template("register.html")

@app.route("/facereg", methods=["GET", "POST"])
def facereg():
    session.clear()
    if request.method == "POST":
        encoded_image = (request.form.get("pic") + "==").encode('utf-8')
        username = request.form.get("name")

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user is None:
            return render_template("camera.html", message=1)

        id_ = user[0]
        decoded_data = zlib.decompress(zlib.compress(encoded_image, 9))
        face_dir = './static/face/unknown'
        os.makedirs(face_dir, exist_ok=True)

        image_path = f'{face_dir}/{id_}.jpg'
        with open(image_path, 'wb') as new_image_handle:
            new_image_handle.write(b64decode(decoded_data))

        try:
            bill_image_path = f'./static/face/{id_}.jpg'
            if not os.path.exists(bill_image_path):
                return render_template("camera.html", message=5)

            bill_face_encoding = face_recognition.face_encodings(face_recognition.load_image_file(bill_image_path))[0]
            unknown_face_encoding = face_recognition.face_encodings(face_recognition.load_image_file(image_path))[0]

            if face_recognition.compare_faces([bill_face_encoding], unknown_face_encoding)[0]:
                session["user_id"] = id_
                return redirect("/")
            else:
                return render_template("camera.html", message=3)

        except Exception:
            return render_template("camera.html", message=5)

    return render_template("camera.html")

@app.route("/facesetup", methods=["GET", "POST"])
def facesetup():
    if request.method == "POST":
        encoded_image = (request.form.get("pic") + "==").encode('utf-8')
        id_ = session["user_id"]

        decoded_data = zlib.decompress(zlib.compress(encoded_image, 9))
        with open(f'./static/face/{id_}.jpg', 'wb') as new_image_handle:
            new_image_handle.write(b64decode(decoded_data))

        try:
            face_recognition.face_encodings(face_recognition.load_image_file(f'./static/face/{id_}.jpg'))[0]
        except IndexError:
            return render_template("face.html", message=1)

        return redirect("/home")

    return render_template("face.html")

# Error handling
def errorhandler(e):
    """Manejar errores"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("error.html", e=e)

# Escuchar errores
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

# Inicialize web
if __name__ == "__main__":
    app.run(debug=True, port=5014)