import os
import zlib
import secrets
import mysql.connector
from mysql.connector import Error as MySQLError
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import face_recognition
from base64 import b64decode
import logging

from helpers import login_required

# Configuración de logging
logging.basicConfig(filename='app.log', level=logging.ERROR, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Configurar la aplicación
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuración de la base de datos
app.config.update(
    MARIADB_HOST="localhost",
    MARIADB_USER="root",
    MARIADB_PASSWORD="whoami",
    MARIADB="mariadb",
    SECRET_KEY=secrets.token_hex(16)
)

def get_db_connection():
    """Obtiene una conexión a la base de datos"""
    try:
        return mysql.connector.connect(
            host=app.config["MARIADB_HOST"],
            user=app.config["MARIADB_USER"],
            password=app.config["MARIADB_PASSWORD"],
            database=app.config["MARIADB"],
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
    except MySQLError as e:
        logging.error(f"Error al conectar a la base de datos: {e}")
        return None

def create_users_table():
    """Crea la tabla de usuarios si no existe"""
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL UNIQUE,
        hash VARCHAR(255) NOT NULL
    )
    """
    execute_query(query)

def execute_query(query, params=None):
    """Ejecuta una consulta en la base de datos"""
    try:
        with get_db_connection() as cnx:
            if cnx is None:
                return None
            with cnx.cursor(dictionary=True) as cursor:
                cursor.execute(query, params or ())
                if query.strip().upper().startswith("SELECT"):
                    return cursor.fetchall()
                cnx.commit()
                return cursor.lastrowid
    except MySQLError as e:
        logging.error(f"Error en la consulta: {e}")
        return None

@app.route("/")
@login_required
def home():
    """Redirige a la página de inicio"""
    return redirect("/home")

@app.route("/home")
@login_required
def index():
    """Renderiza la página de inicio"""
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Maneja el inicio de sesión del usuario"""
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username:
            return render_template("login.html", messager=1)
        if not password:
            return render_template("login.html", messager=2)
        
        user = execute_query("SELECT * FROM users WHERE username = %s", (username,))
        if not user or not check_password_hash(user[0]["hash"], password):
            return render_template("login.html", messager=3)
        
        session["user_id"] = user[0]["id"]
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Cierra la sesión del usuario"""
    session.clear()
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Registra un nuevo usuario"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        if not username:
            return render_template("register.html", messager=1)
        if not password:
            return render_template("register.html", messager=2)
        if not confirmation:
            return render_template("register.html", messager=4)
        if password != confirmation:
            return render_template("register.html", messager=3)
        
        if execute_query("SELECT username FROM users WHERE username = %s", (username,)):
            return render_template("register.html", messager=5)
        
        hashed_password = generate_password_hash(password)
        new_user_id = execute_query("INSERT INTO users (username, hash) VALUES (%s, %s)", (username, hashed_password))
        
        if new_user_id:
            session["user_id"] = new_user_id
            flash(f"Registrado como {username}")
            return redirect("/")
        return render_template("register.html", messager="Error en el proceso de registro")
    return render_template("register.html")

@app.route("/facereg", methods=["GET", "POST"])
def facereg():
    """Maneja el reconocimiento facial"""
    session.clear()
    if request.method == "POST":
        encoded_image = (request.form.get("pic") + "==").encode('utf-8')
        username = request.form.get("name")
        
        user = execute_query("SELECT * FROM users WHERE username = %s", (username,))
        if not user:
            return render_template("camera.html", message=1)
        
        id_ = user[0]['id']
        decoded_data = b64decode(zlib.decompress(zlib.compress(encoded_image, 9)))
        
        dir_path = './static/face/unknown/'
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, f'{id_}.jpg')
        
        with open(file_path, 'wb') as new_image_handle:
            new_image_handle.write(decoded_data)
        
        try:
            known_image = face_recognition.load_image_file(f'./static/face/{id_}.jpg')
            unknown_image = face_recognition.load_image_file(file_path)
            known_encoding = face_recognition.face_encodings(known_image)[0]
            unknown_encoding = face_recognition.face_encodings(unknown_image)[0]
            
            if face_recognition.compare_faces([known_encoding], unknown_encoding)[0]:
                session["user_id"] = id_
                return redirect("/")
            return render_template("camera.html", message=3)
        except Exception as e:
            logging.error(f"Error en el reconocimiento facial: {e}")
            return render_template("camera.html", message="Error en el proceso de reconocimiento facial")
    return render_template("camera.html")

@app.route("/facesetup", methods=["GET", "POST"])
def facesetup():
    """Configura el reconocimiento facial para un usuario"""
    if request.method == "POST":
        encoded_image = (request.form.get("pic") + "==").encode('utf-8')
        user = execute_query("SELECT id FROM users WHERE id = %s", (session["user_id"],))
        
        if not user:
            return render_template("face.html", message=1)
        
        id_ = user[0]["id"]
        decoded_data = b64decode(zlib.decompress(zlib.compress(encoded_image, 9)))
        
        with open(f'./static/face/{id_}.jpg', 'wb') as new_image_handle:
            new_image_handle.write(decoded_data)
        
        try:
            image = face_recognition.load_image_file(f'./static/face/{id_}.jpg')
            face_recognition.face_encodings(image)[0]
            return redirect("/home")
        except Exception as e:
            logging.error(f"Error en la configuración facial: {e}")
            return render_template("face.html", message="Error en el proceso de configuración facial")
    return render_template("face.html")

def errorhandler(e):
    """Maneja los errores"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    logging.error(f"Error: {e}")
    return render_template("error.html", e=e)

# Escuchar errores
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    create_users_table()
    app.run(debug=False)