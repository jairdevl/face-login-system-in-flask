# Import libreries
from flask import Flask, render_template, session, request, redirect
from werkzeug.security import check_password_hash
import mysql.connector
import secrets

# New instance Flask
app = Flask(__name__)

# Settings database
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "whoami"
app.config["MYSQL_DB"] = "database"
app.config["SECRET_KEY"] = secrets.token_bytes(16)

# Connection dabase
cnx = mysql.connector.connect(
    host = app.config["MYSQL_HOST"],
    user = app.config["MYSQL_USER"],
    password = app.config["MYSQL_PASSWORD"],
    database = app.config["MYSQL_DB"],
    charset='utf8mb4',                       
    collation='utf8mb4_unicode_ci' 
)

# Create table database
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

# Define routes
@app.route("/")
def index():
    return redirect("login")

@app.route("/login", methods=['GET', "POST"])
def login():
    # Clean session existing
    session.clear()
    # Check if the from is submitted
    if request.method == "POST":
        input_username = request.form.get("username")
        input_password  = request.form.get("password")
        # Validate field input
        if not input_username:
            render_template("login.html", messager=1)
        elif not input_password:
            render_template("login.html", messager=2)
        # Create cursor to return dictionary
        cursor = cnx.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s',(input_username,))
        user = cursor.fetchone()
        # Validate credencials user
        if user is None or not check_password_hash(user["hash"], input_password):
            return render_template("login.html", messager=3)
        session["user_id"] = user["id"] 
        return redirect("/admin") 
    return render_template("/login.html")
                
# Inicialize web
if __name__ == "__main__":
    app.run()