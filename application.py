import os  # Importar el módulo os para interactuar con el sistema operativo
import zlib  # Importar zlib para la compresión y descompresión de datos
import secrets  # Importar secrets para generar claves secretas
import mysql.connector  # Importar el conector de MySQL para la conexión a la base de datos
from flask import Flask, flash, redirect, render_template, request, session, Response  # Importar componentes de Flask
from flask_session import Session  # Importar la extensión de sesión de Flask
from tempfile import mkdtemp  # Importar mkdtemp para crear directorios temporales
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError  # Importar excepciones de Werkzeug
from werkzeug.security import check_password_hash, generate_password_hash  # Importar funciones de seguridad para el manejo de contraseñas
import face_recognition  # Importar la biblioteca de reconocimiento facial
from base64 import b64decode  # Importar b64decode para decodificar datos en Base64
from helpers import login_required  # Importar un decorador para requerir inicio de sesión

# Configurar la aplicación Flask
app = Flask(__name__)

# Asegurar que las plantillas se recarguen automáticamente
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Asegurar que las respuestas no se almacenen en caché
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configurar la sesión para usar el sistema de archivos (en lugar de cookies firmadas)
app.config["SESSION_FILE_DIR"] = mkdtemp()  # Crear un directorio temporal para almacenar sesiones
app.config["SESSION_PERMANENT"] = False  # Las sesiones no son permanentes
app.config["SESSION_TYPE"] = "filesystem"  # Usar el sistema de archivos para sesiones
Session(app)  # Inicializar la sesión

# Configuración de la base de datos
app.config["MARIADB_HOST"] = "localhost"  # Host de la base de datos
app.config["MARIADB_USER"] = "root"  # Usuario de la base de datos
app.config["MARIADB_PASSWORD"] = "whoami"  # Contraseña de la base de datos
app.config["MARIADB"] = "mariadb"  # Nombre de la base de datos
app.config["SECRET_KEY"] = secrets.token_hex(16)  # Clave secreta para la aplicación

# Función para obtener la conexión a la base de datos
def get_db_connection():
    return mysql.connector.connect(
        host=app.config["MARIADB_HOST"],
        user=app.config["MARIADB_USER"],
        password=app.config["MARIADB_PASSWORD"],
        database=app.config["MARIADB"],
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )

# Crear la tabla de usuarios en la base de datos si no existe
with get_db_connection() as cnx:
    cursor = cnx.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) NOT NULL UNIQUE,
        hash VARCHAR(255) NOT NULL
    )
    """
    cursor.execute(query)  # Ejecutar la consulta para crear la tabla
    cnx.commit()  # Confirmar los cambios en la base de datos

@app.route("/")  # Ruta principal
@login_required  # Requiere que el usuario esté autenticado
def home():
    return redirect("/home")  # Redirigir a la página de inicio

@app.route("/home")  # Ruta para la página de inicio
@login_required  # Requiere que el usuario esté autenticado
def index():
    return render_template("index.html")  # Renderizar la plantilla de inicio

@app.route("/login", methods=["GET", "POST"])  # Ruta para el inicio de sesión
def login():
    """Iniciar sesión del usuario"""
    session.clear()  # Limpiar la sesión existente

    if request.method == "POST":  # Si se envía el formulario
        input_username = request.form.get("username")  # Obtener el nombre de usuario
        input_password = request.form.get("password")  # Obtener la contraseña

        # Validar los campos de entrada
        if not input_username:
            return render_template("login.html", messager=1)  # Mensaje de error si no hay nombre de usuario
        elif not input_password:
            return render_template("login.html", messager=2)  # Mensaje de error si no hay contraseña

        with get_db_connection() as cnx:
            cursor = cnx.cursor(dictionary=True)  # Crear un cursor que devuelva diccionarios
            cursor.execute("SELECT * FROM users WHERE username = %s", (input_username,))  # Consultar el usuario
            user = cursor.fetchone()  # Obtener el usuario

        # Validar las credenciales del usuario
        if user is None or not check_password_hash(user["hash"], input_password):
            return render_template("login.html", messager=3)  # Mensaje de error si las credenciales son incorrectas

        session["user_id"] = user["id"]  # Almacenar el ID del usuario en la sesión
        return redirect("/")  # Redirigir a la página principal

    return render_template("login.html")  # Renderizar la plantilla de inicio de sesión

@app.route("/logout")  # Ruta para cerrar sesión
def logout():
    """Cerrar sesión del usuario"""
    session.clear()  # Limpiar la sesión
    return redirect("/")  # Redirigir a la página principal

@app.route("/register", methods=["GET", "POST"])  # Ruta para el registro de usuarios
def register():
    """Registrar un nuevo usuario"""
    if request.method == "POST":  # Si se envía el formulario
        input_username = request.form.get("username")  # Obtener el nombre de usuario
        input_password = request.form.get("password")  # Obtener la contraseña
        input_confirmation = request.form.get("confirmation")  # Obtener la confirmación de la contraseña

        # Validar los campos de entrada
        if not input_username:
            return render_template("register.html", messager=1)  # Mensaje de error si no hay nombre de usuario
        elif not input_password:
            return render_template("register.html", messager=2)  # Mensaje de error si no hay contraseña
        elif not input_confirmation:
            return render_template("register.html", messager=4)  # Mensaje de error si no hay confirmación
        elif input_password != input_confirmation:
            return render_template("register.html", messager=3)  # Mensaje de error si las contraseñas no coinciden

        with get_db_connection() as cnx:
            cursor = cnx.cursor()  # Crear un cursor
            cursor.execute("SELECT username FROM users WHERE username = %s", (input_username,))  # Consultar si el usuario ya existe
            if cursor.fetchone():
                return render_template("register.html", messager=5)  # Mensaje de error si el usuario ya existe

            # Generar un hash para la contraseña
            hashed_password = generate_password_hash(input_password, method="pbkdf2:sha256", salt_length=8)
            cursor.execute("INSERT INTO users (username, hash) VALUES (%s, %s)", (input_username, hashed_password))  # Insertar el nuevo usuario
            cnx.commit()  # Confirmar los cambios
            new_user_id = cursor.lastrowid  # Obtener el ID del nuevo usuario

        session["user_id"] = new_user_id  # Almacenar el ID del nuevo usuario en la sesión
        flash(f"Registered as {input_username}")  # Mensaje de éxito
        return redirect("/")  # Redirigir a la página principal

    return render_template("register.html")  # Renderizar la plantilla de registro

@app.route("/facereg", methods=["GET", "POST"])  # Ruta para el registro facial
def facereg():
    session.clear()  # Limpiar la sesión
    if request.method == "POST":  # Si se envía el formulario
        encoded_image = (request.form.get("pic") + "==").encode('utf-8')  # Obtener la imagen codificada
        username = request.form.get("name")  # Obtener el nombre de usuario

        with get_db_connection() as cnx:
            cursor = cnx.cursor(dictionary=True)  # Crear un cursor que devuelva diccionarios
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))  # Consultar el usuario
            user = cursor.fetchone()  # Obtener el usuario

        if not user:  # Si el usuario no existe
            return render_template("camera.html", message=1)  # Mensaje de error

        id_ = user['id']  # Obtener el ID del usuario
        compressed_data = zlib.compress(encoded_image, 9)  # Comprimir la imagen
        uncompressed_data = zlib.decompress(compressed_data)  # Descomprimir la imagen
        decoded_data = b64decode(uncompressed_data)  # Decodificar la imagen

        dir_path = './static/face/unknown/'  # Ruta del directorio para imágenes desconocidas
        file_path = os.path.join(dir_path, f'{id_}.jpg')  # Ruta del archivo de imagen

        if not os.path.exists(dir_path):  # Si el directorio no existe
            os.makedirs(dir_path)  # Crear el directorio

        try:
            with open(file_path, 'wb') as new_image_handle:  # Abrir el archivo para escribir
                new_image_handle.write(decoded_data)  # Escribir la imagen en el archivo
        except IOError:
            return render_template("camera.html", message="Error saving image")  # Mensaje de error al guardar la imagen

        try:
            image_of_bill = face_recognition.load_image_file(f'./static/face/{id_}.jpg')  # Cargar la imagen del usuario
            bill_face_encoding = face_recognition.face_encodings(image_of_bill)[0]  # Obtener la codificación facial
        except (FileNotFoundError, IndexError):
            return render_template("camera.html", message=5)  # Mensaje de error si no se encuentra la imagen

        try:
            unknown_image = face_recognition.load_image_file(file_path)  # Cargar la imagen desconocida
            unknown_face_encoding = face_recognition.face_encodings(unknown_image)[0]  # Obtener la codificación facial
        except (FileNotFoundError, IndexError):
            return render_template("camera.html", message=2)  # Mensaje de error si no se encuentra la imagen

        results = face_recognition.compare_faces([bill_face_encoding], unknown_face_encoding)  # Comparar las caras

        if results[0]:  # Si las caras coinciden
            session["user_id"] = user["id"]  # Almacenar el ID del usuario en la sesión
            return redirect("/")  # Redirigir a la página principal
        else:
            return render_template("camera.html", message=3)  # Mensaje de error si las caras no coinciden

    return render_template("camera.html")  # Renderizar la plantilla de la cámara

@app.route("/facesetup", methods=["GET", "POST"])  # Ruta para configurar la cara del usuario
def facesetup():
    if request.method == "POST":  # Si se envía el formulario
        encoded_image = (request.form.get("pic") + "==").encode('utf-8')  # Obtener la imagen codificada

        with get_db_connection() as cnx:
            cursor = cnx.cursor(dictionary=True)  # Crear un cursor que devuelva diccionarios
            cursor.execute("SELECT id FROM users WHERE id = %s", (session["user_id"],))  # Consultar el usuario
            user = cursor.fetchone()  # Obtener el usuario

        if not user:  # Si el usuario no existe
            return render_template("face.html", message=1)  # Mensaje de error

        id_ = user["id"]  # Obtener el ID del usuario
        compressed_data = zlib.compress(encoded_image, 9)  # Comprimir la imagen
        uncompressed_data = zlib.decompress(compressed_data)  # Descomprimir la imagen
        decoded_data = b64decode(uncompressed_data)  # Decodificar la imagen

        with open(f'./static/face/{id_}.jpg', 'wb') as new_image_handle:  # Abrir el archivo para escribir
            new_image_handle.write(decoded_data)  # Escribir la imagen en el archivo

        try:
            image_of_bill = face_recognition.load_image_file(f'./static/face/{id_}.jpg')  # Cargar la imagen del usuario
            face_recognition.face_encodings(image_of_bill)[0]  # Obtener la codificación facial
        except IndexError:
            return render_template("face.html", message=1)  # Mensaje de error si no se encuentra la imagen

        return redirect("/home")  # Redirigir a la página de inicio

    return render_template("face.html")  # Renderizar la plantilla de configuración de la cara

def errorhandler(e):
    """Manejar errores"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()  # Crear un error interno del servidor si no es una excepción HTTP
    return render_template("error.html", e=e)  # Renderizar la plantilla de error

# Escuchar errores
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)  # Registrar el manejador de errores para cada código de excepción

if __name__ == '__main__':
    app.run(debug=True, port=5014)  # Ejecutar la aplicación en modo de depuración en el puerto 5014