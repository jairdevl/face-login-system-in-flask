# Import libreries
from flask import Flask, render_template, request, redirect, url_for
import face_recognition

# New instace Flask
app = Flask(__name__)

# Define routes
@app.route("/")
def index():
    return render_template("index.html")

# Inicialize web
if __name__ == "__main__":
    app.run()