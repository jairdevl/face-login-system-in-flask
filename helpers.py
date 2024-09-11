from functools import wraps
from flask import redirect, render_template, session

def apology(message, code=400):
    """Renderiza un mensaje de disculpa al usuario con el código de estado especificado."""
    
    def escape(s):
        """Escapa caracteres especiales en el mensaje."""
        replacements = {
            "-": "--", " ": "-", "_": "__", "?": "~q",
            "%": "~p", "#": "~h", "/": "~s", '"': "''"
        }
        for old, new in replacements.items():
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """Decora rutas para requerir inicio de sesión."""
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function
