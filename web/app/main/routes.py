from flask import render_template
from flask_login import login_required, current_user

from . import main_bp

@main_bp.route("/")
def menu():
    return render_template("main/menu.html")

@main_bp.route("/protected")
@login_required
def protected():
    return render_template("main/protected.html", user=current_user)
