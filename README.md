# Facial Recognition Login System

A secure authentication system that combines traditional username/password login with facial recognition technology, built with Flask.

![Facial Recognition Login](https://img.shields.io/badge/Security-Facial%20Recognition-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-green)
![Python](https://img.shields.io/badge/Language-Python-yellow)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Security Considerations](#security-considerations)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## 🔍 Overview

This web application provides a robust authentication system that enhances security through facial recognition. Users can register with traditional credentials and then set up facial recognition for subsequent logins, adding an extra layer of security beyond password protection.

## ✨ Features

- **User Registration**: Create an account with username and password
- **Secure Password Storage**: Passwords are hashed before storage
- **Facial Recognition Setup**: Register your face for authentication
- **Dual Authentication Methods**: 
  - Traditional username/password login
  - Facial recognition authentication
- **Responsive UI**: Works on desktop and mobile devices
- **Security Validations**: Input validation and error handling

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Database**: MySQL
- **Authentication**: Werkzeug security for password hashing
- **Facial Recognition**: face_recognition library
- **Frontend**: HTML, CSS, JavaScript

## 📥 Installation

### Prerequisites

- Python 3.6+
- MySQL Server
- pip (Python package manager)
- Webcam (for facial recognition features)

### Step 1: Clone the repository

```bash
git clone https://github.com/yourusername/face-login-system-in-flask.git
cd face-login-system-in-flask
```

### Step 2: Create and activate a virtual environment (recommended)

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install flask face_recognition mysql-connector-python werkzeug
```

Note: The `face_recognition` library requires `dlib` which may need additional system dependencies. Refer to the [dlib installation guide](https://github.com/davisking/dlib) if you encounter issues.

### Step 4: Set up the MySQL database

```bash
# Log in to MySQL
mysql -u root -p

# Create a database
CREATE DATABASE database;
```

### Step 5: Configure the application

Update the database connection details in `app.py`:

```python
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "your_password"
app.config["MYSQL_DB"] = "database"
```

### Step 6: Run the application

```bash
python app.py
```

The application will be available at `http://localhost:5000`.

## 🚀 Usage

1. **Register a new account**:
   - Navigate to the registration page
   - Create a username and password
   - Submit the form

2. **Set up facial recognition**:
   - After registration, you'll be redirected to the admin page
   - Click on the facial recognition setup option
   - Position your face in the camera frame
   - Capture your image for facial recognition

3. **Login with facial recognition**:
   - Go to the login page
   - Enter your username
   - Choose facial recognition login
   - Allow camera access
   - The system will authenticate you by matching your face

## 🔒 Security Considerations

- Facial recognition is an additional security layer, not a replacement for passwords
- Passwords are securely hashed using Werkzeug security
- Face matching uses a precise threshold (0.4) to minimize false positives
- Error handling prevents common security vulnerabilities

## 📁 Project Structure

```
face-login-system-in-flask/
├── app.py               # Main application file
├── static/              # Static files (JS, images)
│   ├── js/              # JavaScript files
│   └── face/            # Stored facial images
├── templates/           # HTML templates
│   ├── admin.html       # Admin dashboard
│   ├── camera.html      # Facial recognition login
│   ├── face.html        # Facial setup page
│   ├── layout.html      # Base template
│   ├── login.html       # Login page
│   └── register.html    # Registration page
└── README.md            # Project documentation
```

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
